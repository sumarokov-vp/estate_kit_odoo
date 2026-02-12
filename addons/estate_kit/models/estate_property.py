import logging
import requests

from odoo import api, fields, models
from odoo.exceptions import UserError

from ..services.api_client import EstateKitApiClient

_logger = logging.getLogger(__name__)

SYNC_FIELDS = {"external_id", "pending_sync", "last_synced_at"}

PULL_PAGE_LIMIT = 100

API_PROPERTY_TYPE_MAP = {
    1: "apartment",
    2: "house",
    3: "townhouse",
    4: "commercial",
    5: "land",
}

API_DEAL_TYPE_MAP = {
    1: "sale",
    2: "rent_long",
    3: "rent_daily",
}

API_STATE_MAP = {
    1: "new",
    2: "ready",
    3: "published",
    4: "unpublished",
}


class EstateProperty(models.Model):
    _name = "estate.property"
    _description = "Объект недвижимости"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "create_date desc"

    # === Основные ===
    name = fields.Char(string="Название", required=True, tracking=True)
    description = fields.Text(string="Описание")
    active = fields.Boolean(default=True)

    property_type = fields.Selection(
        [
            ("apartment", "Квартира"),
            ("house", "Дом"),
            ("townhouse", "Таунхаус"),
            ("commercial", "Коммерция"),
            ("land", "Земля"),
        ],
        string="Тип объекта",
        required=True,
        default="apartment",
        tracking=True,
    )
    deal_type = fields.Selection(
        [
            ("sale", "Продажа"),
            ("rent_long", "Долгосрочная аренда"),
            ("rent_daily", "Посуточная аренда"),
        ],
        string="Тип сделки",
        required=True,
        default="sale",
        tracking=True,
    )
    state = fields.Selection(
        [
            ("new", "Новый"),
            ("ready", "Готов к публикации"),
            ("published", "Опубликован"),
            ("unpublished", "Снят с публикации"),
        ],
        string="Стадия",
        required=True,
        copy=False,
        default="new",
        tracking=True,
    )

    price = fields.Monetary(string="Цена", tracking=True)
    currency_id = fields.Many2one(
        "res.currency",
        default=lambda self: self.env.company.currency_id,
    )
    rooms = fields.Integer(string="Комнат")
    bedrooms = fields.Integer(string="Спален")
    area_total = fields.Float(string="Общая площадь (м²)")

    # === Адрес ===
    city_id = fields.Many2one(
        "estate.city",
        string="Город",
        default=lambda self: self._default_city(),
        tracking=True,
    )
    district_id = fields.Many2one(
        "estate.district",
        string="Район",
        domain="[('city_id', '=', city_id)]",
        tracking=True,
    )
    street_id = fields.Many2one(
        "estate.street",
        string="Улица",
        domain="[('city_id', '=', city_id)]",
    )
    house_number = fields.Char(string="Дом")
    apartment_number = fields.Char(string="Квартира")

    # === Геолокация ===
    latitude = fields.Float(string="Широта", digits=(10, 7))
    longitude = fields.Float(string="Долгота", digits=(10, 7))
    geo_address = fields.Char(
        string="Адрес для геокодирования",
        compute="_compute_geo_address",
        store=True,
    )

    @api.model_create_multi
    def create(self, vals_list):
        result = super().create(vals_list)
        if not self.env.context.get("skip_api_sync"):
            auto_mls = (
                self.env["ir.config_parameter"]
                .sudo()
                .get_param("estate_kit.auto_mls", "True")
            )
            if auto_mls == "True":
                result.with_context(skip_api_sync=True).write({"mls_listed": True})
            for record in result:
                record._push_to_api()
        return result

    def write(self, vals):
        if "state" in vals:
            new_state = vals["state"]
            is_forced = self.env.context.get("force_state_change")
            if not is_forced:
                for record in self:
                    if record.state == "new" and new_state == "ready":
                        raise UserError(
                            "Используйте кнопку «Готов к публикации» для смены статуса."
                        )
                    if new_state == "published":
                        raise UserError(
                            "Публикация объекта возможна только через специальное действие (API, выгрузка)."
                        )
                    if new_state == "unpublished":
                        raise UserError(
                            "Снятие с публикации возможно только через специальное действие."
                        )
        result = super().write(vals)
        should_sync = (
            not self.env.context.get("skip_api_sync")
            and not SYNC_FIELDS.issuperset(vals.keys())
        )
        if should_sync:
            for record in self:
                record._push_to_api()
        return result

    def action_set_ready(self):
        for record in self:
            if record.state != "new":
                raise UserError(
                    "Перевести в «Готов к публикации» можно только новый объект."
                )
        self.with_context(force_state_change=True).write({"state": "ready"})

    def action_publish(self):
        for record in self:
            if record.state != "ready":
                raise UserError(
                    "Опубликовать можно только объект в статусе «Готов к публикации»."
                )
        self.with_context(force_state_change=True).write({"state": "published"})

    def action_unpublish(self):
        for record in self:
            if record.state != "published":
                raise UserError(
                    "Снять с публикации можно только опубликованный объект."
                )
        self.with_context(force_state_change=True).write({"state": "unpublished"})

    @api.depends("city_id", "district_id", "street_id", "house_number")
    def _compute_geo_address(self):
        for record in self:
            parts = []
            if record.city_id:
                parts.append(record.city_id.name)
            if record.district_id:
                parts.append(record.district_id.name)
            if record.street_id:
                parts.append(record.street_id.name)
            if record.house_number:
                parts.append(record.house_number)
            record.geo_address = ", ".join(parts) if parts else False

    @api.model
    def _default_city(self):
        return self.env["estate.city"].search([("code", "=", "almaty")], limit=1)

    @api.onchange("city_id")
    def _onchange_city_id(self):
        if self.district_id and self.district_id.city_id != self.city_id:
            self.district_id = False
        if self.street_id and self.street_id.city_id != self.city_id:
            self.street_id = False

    def action_detect_district(self):
        self.ensure_one()
        api_key = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("estate_kit.yandex_geocoder_api_key")
        )
        if not api_key:
            raise UserError("API ключ Yandex Geocoder не настроен")

        address_parts = []
        if self.city_id:
            address_parts.append(self.city_id.name)
        if self.street_id:
            address_parts.append(self.street_id.name)
        if self.house_number:
            address_parts.append(self.house_number)

        if not address_parts:
            raise UserError("Укажите адрес для определения района")

        address = ", ".join(address_parts)

        # Шаг 1: Прямое геокодирование — получаем координаты
        response = requests.get(
            "https://geocode-maps.yandex.ru/1.x/",
            params={"apikey": api_key, "geocode": address, "format": "json"},
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()

        feature_members = (
            data.get("response", {})
            .get("GeoObjectCollection", {})
            .get("featureMember", [])
        )
        if not feature_members:
            raise UserError(f"Адрес не найден: {address}")

        geo_object = feature_members[0].get("GeoObject", {})
        pos = geo_object.get("Point", {}).get("pos", "")
        if not pos:
            raise UserError(f"Координаты не найдены для адреса: {address}")

        lon, lat = pos.split()
        lon, lat = float(lon), float(lat)

        if not self.latitude or not self.longitude:
            self.latitude = lat
            self.longitude = lon

        # Шаг 2: Обратное геокодирование с kind=district — получаем район
        response = requests.get(
            "https://geocode-maps.yandex.ru/1.x/",
            params={
                "apikey": api_key,
                "geocode": f"{lon},{lat}",
                "format": "json",
                "kind": "district",
            },
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()

        feature_members = (
            data.get("response", {})
            .get("GeoObjectCollection", {})
            .get("featureMember", [])
        )

        district_name = None
        for feature in feature_members:
            name = feature.get("GeoObject", {}).get("name", "")
            if "район" in name.lower() and "жилой" not in name.lower():
                district_name = name
                break

        if not district_name:
            for feature in feature_members:
                components = (
                    feature.get("GeoObject", {})
                    .get("metaDataProperty", {})
                    .get("GeocoderMetaData", {})
                    .get("Address", {})
                    .get("Components", [])
                )
                for comp in components:
                    if comp.get("kind") == "district":
                        name = comp.get("name", "")
                        if "район" in name.lower() and "жилой" not in name.lower():
                            district_name = name
                            break
                if district_name:
                    break

        if district_name and self.city_id:
            district = self.env["estate.district"].search(
                [("name", "ilike", district_name), ("city_id", "=", self.city_id.id)],
                limit=1,
            )
            if not district:
                district = self.env["estate.district"].create(
                    {"name": district_name, "city_id": self.city_id.id}
                )
            self.district_id = district.id
        else:
            _logger.warning("Район не найден для адреса: %s", address)

    # === Характеристики строения ===
    floor = fields.Integer(string="Этаж")
    floors_total = fields.Integer(string="Этажность")
    year_built = fields.Integer(string="Год постройки")
    building_type = fields.Selection(
        [
            ("panel", "Панельный"),
            ("brick", "Кирпичный"),
            ("monolith", "Монолит"),
            ("metal_frame", "Металлокаркас"),
            ("wood", "Деревянный"),
        ],
        string="Тип строения",
    )
    ceiling_height = fields.Float(string="Высота потолков (м)")
    entrance = fields.Integer(string="Подъезд")
    wall_material = fields.Selection(
        [
            ("brick", "Кирпич"),
            ("gas_block", "Газоблок"),
            ("wood", "Дерево"),
            ("sip", "СИП-панели"),
            ("frame", "Каркас"),
            ("polystyrene", "Полистиролбетон"),
        ],
        string="Материал стен",
    )
    roof_type = fields.Selection(
        [
            ("flat", "Плоская"),
            ("gable", "Двускатная"),
            ("hip", "Вальмовая"),
        ],
        string="Тип крыши",
    )
    foundation = fields.Selection(
        [
            ("strip", "Ленточный"),
            ("slab", "Плитный"),
            ("pile", "Свайный"),
        ],
        string="Фундамент",
    )

    # === Площади ===
    area_living = fields.Float(string="Жилая площадь (м²)")
    area_kitchen = fields.Float(string="Площадь кухни (м²)")
    area_land = fields.Float(string="Площадь участка (сотки)")
    area_commercial = fields.Float(string="Торговая площадь (м²)")
    area_warehouse = fields.Float(string="Складская площадь (м²)")

    # === Удобства ===
    bathroom = fields.Selection(
        [
            ("combined", "Совмещённый"),
            ("separate", "Раздельный"),
        ],
        string="Санузел",
    )
    bathroom_count = fields.Integer(string="Количество санузлов")
    balcony = fields.Selection(
        [
            ("none", "Нет"),
            ("balcony", "Балкон"),
            ("loggia", "Лоджия"),
            ("terrace", "Терраса"),
        ],
        string="Балкон",
    )
    balcony_glazed = fields.Boolean(string="Балкон застеклён")
    parking = fields.Selection(
        [
            ("none", "Нет"),
            ("yard", "Двор"),
            ("underground", "Подземная"),
            ("garage", "Гараж"),
            ("ground", "Наземная"),
        ],
        string="Парковка",
    )
    parking_count = fields.Integer(string="Количество парковок")
    furniture = fields.Selection(
        [
            ("none", "Без мебели"),
            ("partial", "Частично"),
            ("full", "Полная"),
        ],
        string="Мебель",
    )
    condition = fields.Selection(
        [
            ("no_repair", "Без ремонта"),
            ("cosmetic", "Косметический"),
            ("euro", "Евроремонт"),
            ("designer", "Дизайнерский"),
        ],
        string="Состояние",
    )

    # === Коммуникации ===
    heating = fields.Selection(
        [
            ("central", "Центральное"),
            ("autonomous", "Автономное"),
            ("none", "Нет"),
        ],
        string="Отопление",
    )
    water = fields.Selection(
        [
            ("central", "Центральное"),
            ("well", "Скважина/колодец"),
            ("none", "Нет"),
        ],
        string="Водоснабжение",
    )
    sewage = fields.Selection(
        [
            ("central", "Центральная"),
            ("septic", "Септик"),
            ("none", "Нет"),
        ],
        string="Канализация",
    )
    gas = fields.Selection(
        [
            ("central", "Центральный"),
            ("balloon", "Баллон"),
            ("gas_tank", "Газгольдер"),
            ("none", "Нет"),
        ],
        string="Газ",
    )
    electricity = fields.Selection(
        [
            ("yes", "Есть"),
            ("nearby", "Рядом"),
            ("none", "Нет"),
        ],
        string="Электричество",
    )
    internet = fields.Selection(
        [
            ("none", "Нет"),
            ("wired", "Проводной"),
            ("fiber", "Оптика"),
            ("dsl", "DSL"),
            ("mobile", "Мобильный (4G/5G)"),
        ],
        string="Интернет",
    )

    # === Безопасность ===
    security_intercom = fields.Boolean(string="Домофон")
    security_alarm = fields.Boolean(string="Сигнализация")
    security_guard = fields.Boolean(string="Охрана")
    security_video = fields.Boolean(string="Видеонаблюдение")
    security_coded_lock = fields.Boolean(string="Кодовый замок")
    security_concierge = fields.Boolean(string="Консьерж")
    security_fire_alarm = fields.Boolean(string="Пожарная сигнализация")

    # === Особенности ===
    window_type = fields.Selection(
        [
            ("plastic", "Пластиковые"),
            ("wood", "Деревянные"),
            ("aluminum", "Алюминиевые"),
        ],
        string="Окна",
    )
    climate_equipment_ids = fields.Many2many(
        "estate.climate.equipment",
        string="Климатическое оборудование",
    )
    appliance_ids = fields.Many2many(
        "estate.appliance",
        string="Бытовая техника",
    )
    not_corner = fields.Boolean(string="Не угловая")
    isolated_rooms = fields.Boolean(string="Изолированные комнаты")
    storage = fields.Boolean(string="Кладовка")
    quiet_yard = fields.Boolean(string="Тихий двор")
    kitchen_studio = fields.Boolean(string="Кухня-студия")
    new_plumbing = fields.Boolean(string="Новая сантехника")
    built_in_kitchen = fields.Boolean(string="Встроенная кухня")

    # === Юридическое ===
    is_pledged = fields.Boolean(string="В залоге")
    is_privatized = fields.Boolean(string="Приватизирована")
    documents_ready = fields.Boolean(string="Документы готовы к сделке")
    ownership_type = fields.Selection(
        [
            ("private", "Частная собственность"),
            ("shared", "Долевая собственность"),
            ("state", "Государственная"),
        ],
        string="Тип собственности",
    )
    encumbrance = fields.Boolean(string="Обременение")

    # === Коммерческая недвижимость ===
    commercial_type = fields.Selection(
        [
            ("office", "Офис"),
            ("retail", "Торговое"),
            ("warehouse", "Склад"),
            ("production", "Производство"),
        ],
        string="Назначение",
    )
    has_showcase = fields.Boolean(string="Витрины")
    separate_entrance = fields.Boolean(string="Отдельный вход")
    electricity_power = fields.Integer(string="Мощность электричества (кВт)")

    # === Земельные участки ===
    land_category = fields.Selection(
        [
            ("izhs", "ИЖС"),
            ("snt", "СНТ"),
            ("lpkh", "ЛПХ"),
            ("commercial", "Коммерческое"),
        ],
        string="Категория земли",
    )
    land_status = fields.Selection(
        [
            ("owned", "В собственности"),
            ("leased", "В аренде"),
        ],
        string="Статус земли",
    )
    communications_nearby = fields.Boolean(string="Коммуникации рядом")
    road_access = fields.Selection(
        [
            ("asphalt", "Асфальт"),
            ("gravel", "Гравий"),
            ("dirt", "Грунтовая"),
            ("none", "Нет"),
        ],
        string="Подъездная дорога",
    )

    # === Собственник и договор ===
    owner_id = fields.Many2one("res.partner", string="Собственник", tracking=True)
    owner_name = fields.Char(string="Имя владельца", help="Имя владельца из бота")
    source_id = fields.Many2one("estate.source", string="Источник")
    contract_type = fields.Selection(
        [
            ("exclusive", "Эксклюзив"),
            ("non_exclusive", "Не эксклюзив"),
        ],
        string="Тип договора",
    )
    contract_start = fields.Date(string="Начало договора")
    contract_end = fields.Date(string="Окончание договора")

    # === Ответственные ===
    user_id = fields.Many2one(
        "res.users",
        string="Ответственный",
        default=lambda self: self.env.user,
        tracking=True,
    )
    listing_coordinator_id = fields.Many2one(
        "res.users",
        string="Координатор листинга",
        help="Кто внёс объект в базу",
    )
    listing_agent_id = fields.Many2one(
        "res.users",
        string="Листинг-агент",
    )

    # === Служебное ===
    is_shared = fields.Boolean(
        string="Открытый объект",
        help="Объект доступен другим агентам",
    )
    internal_note = fields.Text(string="Внутренние заметки")
    video_url = fields.Char(string="Видео")
    instagram_url = fields.Char(string="Instagram")
    krisha_url = fields.Char(string="URL на Krisha.kz")

    # === Синхронизация ===
    external_id = fields.Integer(string="API ID", index=True, copy=False, readonly=True)
    pending_sync = fields.Boolean(string="Pending Sync", default=False, copy=False, readonly=True)
    last_synced_at = fields.Datetime(string="Last Synced", copy=False, readonly=True)

    # === MLS ===
    mls_listed = fields.Boolean(string="В MLS", default=False, copy=False)
    mls_status = fields.Selection(
        [
            ("not_listed", "Не размещён"),
            ("listed", "В MLS"),
            ("received", "Получен из MLS"),
        ],
        string="Статус MLS",
        compute="_compute_mls_status",
        store=False,
    )
    api_configured = fields.Boolean(
        compute="_compute_api_configured",
        store=False,
    )

    # === Медиа ===
    image_ids = fields.One2many(
        "estate.property.image",
        "property_id",
        string="Фотографии",
    )

    @api.depends("external_id", "mls_listed")
    def _compute_mls_status(self):
        for record in self:
            if record.external_id and not record.mls_listed:
                record.mls_status = "received"
            elif record.mls_listed:
                record.mls_status = "listed"
            else:
                record.mls_status = "not_listed"

    def _compute_api_configured(self):
        api_url = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("estate_kit.api_url", "")
        )
        configured = bool(api_url)
        for record in self:
            record.api_configured = configured

    def action_publish_to_mls(self):
        self.with_context(skip_api_sync=True).write({"mls_listed": True})
        for record in self:
            record._push_to_api()

    def action_unpublish_from_mls(self):
        self.with_context(skip_api_sync=True).write({"mls_listed": False})
        for record in self:
            record._push_to_api()

    @api.model
    def _cron_retry_pending_sync(self):
        pending = self.search([("pending_sync", "=", True)])
        _logger.info("Retry pending sync: found %d records", len(pending))
        for record in pending:
            record._push_to_api()

    def _push_owner_to_api(self):
        self.ensure_one()
        if not self.owner_id:
            return None
        partner = self.owner_id
        client = EstateKitApiClient(self.env)
        if not client._is_configured:
            return None
        payload = {"name": partner.name, "phone": partner.phone or ""}
        try:
            if partner.external_owner_id:
                client.put(f"/owners/{partner.external_owner_id}", payload)
                return partner.external_owner_id
            response = client.post("/owners", payload)
            if response and "id" in response:
                partner.write({"external_owner_id": response["id"]})
                return response["id"]
        except Exception:
            _logger.exception(
                "Failed to push owner %s (id=%s) to API", partner.name, partner.id
            )
        return None

    def _push_to_api(self):
        self.ensure_one()
        client = EstateKitApiClient(self.env)
        if not client._is_configured:
            return

        self._push_owner_to_api()
        payload = self._prepare_api_payload()

        try:
            if self.external_id:
                client.put(f"/properties/{self.external_id}", payload)
            else:
                response = client.post("/properties", payload)
                if response and response.get("id"):
                    self.with_context(skip_api_sync=True).write(
                        {"external_id": response["id"]}
                    )
            self.with_context(skip_api_sync=True).write(
                {"pending_sync": False, "last_synced_at": fields.Datetime.now()}
            )
        except Exception:
            _logger.exception(
                "Failed to push property %s (id=%s) to API", self.name, self.id
            )
            self.with_context(skip_api_sync=True).write({"pending_sync": True})

    def _prepare_api_payload(self):
        self.ensure_one()

        payload = {
            "name": self.name,
            "description": self.description or "",
            "property_type": self.property_type,
            "deal_type": self.deal_type,
            "state": self.state,
            "price": self.price,
            "currency": self.currency_id.name if self.currency_id else "KZT",
            "rooms": self.rooms,
            "bedrooms": self.bedrooms,
            "area": self.area_total,
            "area_living": self.area_living,
            "area_kitchen": self.area_kitchen,
            "area_land": self.area_land,
            "house_number": self.house_number or "",
            "apartment_number": self.apartment_number or "",
            "latitude": self.latitude,
            "longitude": self.longitude,
            "floor": self.floor,
            "floors_total": self.floors_total,
            "year_built": self.year_built,
            "building_type": self.building_type or "",
            "ceiling_height": self.ceiling_height,
            "wall_material": self.wall_material or "",
            "roof_type": self.roof_type or "",
            "foundation": self.foundation or "",
            "bathroom": self.bathroom or "",
            "bathroom_count": self.bathroom_count,
            "balcony": self.balcony or "",
            "balcony_glazed": self.balcony_glazed,
            "parking": self.parking or "",
            "parking_count": self.parking_count,
            "furniture": self.furniture or "",
            "condition": self.condition or "",
            "heating": self.heating or "",
            "water": self.water or "",
            "sewage": self.sewage or "",
            "gas": self.gas or "",
            "electricity": self.electricity or "",
            "internet": self.internet or "",
            "window_type": self.window_type or "",
            "entrance": self.entrance,
            "not_corner": self.not_corner,
            "isolated_rooms": self.isolated_rooms,
            "storage": self.storage,
            "quiet_yard": self.quiet_yard,
            "kitchen_studio": self.kitchen_studio,
            "new_plumbing": self.new_plumbing,
            "built_in_kitchen": self.built_in_kitchen,
            "security_intercom": self.security_intercom,
            "security_alarm": self.security_alarm,
            "security_guard": self.security_guard,
            "security_video": self.security_video,
            "security_coded_lock": self.security_coded_lock,
            "security_concierge": self.security_concierge,
            "security_fire_alarm": self.security_fire_alarm,
            "is_pledged": self.is_pledged,
            "is_privatized": self.is_privatized,
            "documents_ready": self.documents_ready,
            "ownership_type": self.ownership_type or "",
            "encumbrance": self.encumbrance,
            "commercial_type": self.commercial_type or "",
            "area_commercial": self.area_commercial,
            "area_warehouse": self.area_warehouse,
            "has_showcase": self.has_showcase,
            "separate_entrance": self.separate_entrance,
            "electricity_power": self.electricity_power,
            "land_category": self.land_category or "",
            "land_status": self.land_status or "",
            "communications_nearby": self.communications_nearby,
            "road_access": self.road_access or "",
            "is_shared": self.mls_listed,
            "video_url": self.video_url or "",
            "contract_type": self.contract_type or "",
            "contract_start": (
                self.contract_start.isoformat() if self.contract_start else None
            ),
            "contract_end": (
                self.contract_end.isoformat() if self.contract_end else None
            ),
            "owner_name": self.owner_name or "",
        }

        if self.owner_id and self.owner_id.external_owner_id:
            payload["owner_id"] = self.owner_id.external_owner_id

        if self.city_id:
            payload["city_id"] = self.city_id.id
        if self.district_id:
            payload["district_id"] = self.district_id.id
        if self.street_id:
            payload["street_id"] = self.street_id.id
        if self.source_id:
            payload["source"] = self.source_id.code or self.source_id.name

        payload["climate_equipment"] = [
            eq.code or eq.name for eq in self.climate_equipment_ids
        ]
        payload["appliances"] = [ap.code or ap.name for ap in self.appliance_ids]

        return payload

    @api.model
    def _find_or_create_owner_from_api(self, owner_data):
        if not owner_data or not owner_data.get("id"):
            return False
        external_id = owner_data["id"]
        partner = self.env["res.partner"].search(
            [("external_owner_id", "=", external_id)], limit=1
        )
        vals = {
            "name": owner_data.get("name", ""),
            "phone": owner_data.get("phone", ""),
            "external_owner_id": external_id,
        }
        if partner:
            partner.write({"name": vals["name"], "phone": vals["phone"]})
            return partner.id
        return self.env["res.partner"].create(vals).id

    @api.model
    def get_twogis_api_key(self):
        return (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("estate_kit.twogis_api_key", "")
        )

    @api.model
    def _cron_pull_from_api(self):
        client = EstateKitApiClient(self.env)
        if not client._is_configured:
            return

        config = self.env["ir.config_parameter"].sudo()
        last_sync = config.get_param("estate_kit.last_sync", "")

        offset = 0
        total_created = 0
        total_updated = 0

        while True:
            params = {"limit": PULL_PAGE_LIMIT, "offset": offset}
            if last_sync:
                params["updated_after"] = last_sync

            response = client.get("/properties", params=params)
            if not response:
                _logger.error("Failed to fetch properties from API (offset=%d)", offset)
                break

            items = response.get("items", [])
            if not items:
                break

            for item in items:
                created, updated = self._process_api_item(item)
                total_created += created
                total_updated += updated

            if len(items) < PULL_PAGE_LIMIT:
                break

            offset += PULL_PAGE_LIMIT

        config.set_param("estate_kit.last_sync", fields.Datetime.now())
        _logger.info(
            "Pull from API completed: %d created, %d updated",
            total_created,
            total_updated,
        )

    def _process_api_item(self, item):
        api_id = item.get("id")
        if not api_id:
            return 0, 0

        existing = self.search([("external_id", "=", api_id)], limit=1)

        api_updated_at = item.get("updated_at")
        if existing and api_updated_at and existing.last_synced_at:
            api_dt = fields.Datetime.to_datetime(
                api_updated_at.replace("Z", "+00:00")
            )
            if api_dt and api_dt <= existing.last_synced_at:
                return 0, 0

        vals = self._import_from_api_data(item)
        sync_ctx = self.with_context(skip_api_sync=True, force_state_change=True)

        if existing:
            sync_ctx.browse(existing.id).write(vals)
            existing.with_context(skip_api_sync=True).write(
                {"last_synced_at": fields.Datetime.now()}
            )
            self.env["estate.property.image"]._pull_images_for_property(existing)
            return 0, 1

        vals["external_id"] = api_id
        vals["last_synced_at"] = fields.Datetime.now()
        new_record = sync_ctx.create(vals)
        self.env["estate.property.image"]._pull_images_for_property(new_record)
        return 1, 0

    @api.model
    def _handle_webhook_property_created(self, payload):
        property_id = payload.get("data", {}).get("property_id")
        if not property_id:
            _logger.warning("Webhook property.created: missing property_id in payload")
            return

        client = EstateKitApiClient(self.env)
        item = client.get(f"/properties/{property_id}")
        if not item:
            _logger.warning(
                "Webhook property.created: failed to fetch property %d from API",
                property_id,
            )
            return

        created, updated = self._process_api_item(item)
        _logger.info(
            "Webhook property.created: property_id=%d, created=%d, updated=%d",
            property_id,
            created,
            updated,
        )

    @api.model
    def _handle_webhook_property_transition(self, payload):
        data = payload.get("data", {})
        property_id = data.get("property_id")
        status_id = data.get("status_id")

        if not property_id:
            _logger.warning("Webhook property.transition: missing property_id in payload")
            return

        new_state = API_STATE_MAP.get(status_id)
        if not new_state:
            _logger.warning(
                "Webhook property.transition: unknown status_id=%s for property %d",
                status_id,
                property_id,
            )
            return

        existing = self.search([("external_id", "=", property_id)], limit=1)
        if existing:
            existing.with_context(
                skip_api_sync=True, force_state_change=True
            ).write({"state": new_state})
            _logger.info(
                "Webhook property.transition: property %d state → %s",
                property_id,
                new_state,
            )
            return

        _logger.info(
            "Webhook property.transition: property %d not found locally, fetching from API",
            property_id,
        )
        client = EstateKitApiClient(self.env)
        item = client.get(f"/properties/{property_id}")
        if item:
            self._process_api_item(item)

    @api.model
    def _handle_webhook_contact_request(self, payload):
        data = payload.get("data", {})
        property_id = data.get("property_id")
        if not property_id:
            _logger.warning("contact_request.received: missing property_id in payload")
            return

        prop = self.search([("external_id", "=", property_id)], limit=1)
        if not prop:
            _logger.warning(
                "contact_request.received: property with external_id=%s not found",
                property_id,
            )
            return

        responsible_user = prop.user_id or prop.listing_agent_id
        if not responsible_user:
            _logger.warning(
                "contact_request.received: no responsible user for property id=%s",
                prop.id,
            )
            return

        requester_tenant_id = data.get("requester_tenant_id")
        note = "Запрос контакта собственника"
        if requester_tenant_id:
            note += f" (tenant_id: {requester_tenant_id})"

        activity_type = self.env.ref("mail.mail_activity_data_todo")
        self.env["mail.activity"].create({
            "activity_type_id": activity_type.id,
            "summary": "Запрос контакта собственника",
            "note": note,
            "res_model_id": self.env["ir.model"]._get_id("estate.property"),
            "res_id": prop.id,
            "user_id": responsible_user.id,
        })

        _logger.info(
            "contact_request.received: created activity for property id=%s, user=%s",
            prop.id,
            responsible_user.login,
        )

    @api.model
    def _handle_webhook_mls_new_listing(self, payload):
        property_id = payload.get("data", {}).get("property_id")
        if not property_id:
            _logger.warning("mls.new_listing: missing property_id in payload")
            return

        existing = self.search([("external_id", "=", property_id)], limit=1)
        if existing:
            _logger.info("mls.new_listing: property with external_id=%d already exists", property_id)
            return

        client = EstateKitApiClient(self.env)
        item = client.get(f"/mls/properties/{property_id}")
        if not item:
            _logger.warning("mls.new_listing: failed to fetch property %d from API", property_id)
            return

        vals = self._import_from_api_data(item)
        vals["external_id"] = property_id
        vals["mls_listed"] = False
        vals["last_synced_at"] = fields.Datetime.now()
        self.with_context(skip_api_sync=True, force_state_change=True).create(vals)
        _logger.info("mls.new_listing: created property with external_id=%d", property_id)

    @api.model
    def _handle_webhook_mls_listing_updated(self, payload):
        property_id = payload.get("data", {}).get("property_id")
        if not property_id:
            _logger.warning("mls.listing_updated: missing property_id in payload")
            return

        existing = self.search([("external_id", "=", property_id)], limit=1)
        if not existing:
            _logger.warning(
                "mls.listing_updated: property with external_id=%d not found", property_id
            )
            return

        client = EstateKitApiClient(self.env)
        item = client.get(f"/mls/properties/{property_id}")
        if not item:
            _logger.warning(
                "mls.listing_updated: failed to fetch property %d from API", property_id
            )
            return

        vals = self._import_from_api_data(item)
        existing.with_context(skip_api_sync=True, force_state_change=True).write(vals)
        existing.with_context(skip_api_sync=True).write(
            {"last_synced_at": fields.Datetime.now()}
        )
        _logger.info("mls.listing_updated: updated property with external_id=%d", property_id)

    @api.model
    def _handle_webhook_mls_listing_removed(self, payload):
        property_id = payload.get("data", {}).get("property_id")
        if not property_id:
            _logger.warning("mls.listing_removed: missing property_id in payload")
            return

        existing = self.search([("external_id", "=", property_id)], limit=1)
        if not existing:
            _logger.warning(
                "mls.listing_removed: property with external_id=%d not found", property_id
            )
            return

        existing.with_context(skip_api_sync=True).write({"active": False})
        _logger.info("mls.listing_removed: deactivated property with external_id=%d", property_id)

    @api.model
    def _import_from_api_data(self, data):
        vals = {}

        property_type = API_PROPERTY_TYPE_MAP.get(data.get("property_type_id"))
        if property_type:
            vals["property_type"] = property_type

        deal_type = API_DEAL_TYPE_MAP.get(data.get("deal_type_id"))
        if deal_type:
            vals["deal_type"] = deal_type

        state = API_STATE_MAP.get(data.get("status_id"))
        if state:
            vals["state"] = state

        if data.get("description"):
            vals["description"] = data["description"]

        if data.get("price") is not None:
            vals["price"] = float(data["price"])

        if data.get("area") is not None:
            vals["area_total"] = float(data["area"])

        if data.get("owner_name"):
            vals["owner_name"] = data["owner_name"]

        owner_api_id = data.get("owner_id")
        if owner_api_id:
            owner = self.env["res.partner"].search(
                [("external_owner_id", "=", owner_api_id)], limit=1
            )
            if owner:
                vals["owner_id"] = owner.id
            else:
                _logger.warning(
                    "Owner with API ID %d not found, skipping", owner_api_id
                )

        location = data.get("location") or {}
        self._import_location(vals, location)

        if not vals.get("name"):
            vals["name"] = self._generate_name_from_vals(vals)

        return vals

    @api.model
    def _import_location(self, vals, location):
        if not location:
            return

        city_ext_id = location.get("city_id")
        if city_ext_id:
            city = self.env["estate.city"].search(
                [("external_id", "=", city_ext_id)], limit=1
            )
            if city:
                vals["city_id"] = city.id
            else:
                _logger.warning("City with API ID %d not found, skipping", city_ext_id)

        district_ext_id = location.get("district_id")
        if district_ext_id:
            district = self.env["estate.district"].search(
                [("external_id", "=", district_ext_id)], limit=1
            )
            if district:
                vals["district_id"] = district.id
            else:
                _logger.warning(
                    "District with API ID %d not found, skipping", district_ext_id
                )

        street_name = location.get("street")
        if street_name and vals.get("city_id"):
            street = self.env["estate.street"].search(
                [("name", "=", street_name), ("city_id", "=", vals["city_id"])],
                limit=1,
            )
            if street:
                vals["street_id"] = street.id

        if location.get("house_number"):
            vals["house_number"] = location["house_number"]

        if location.get("apartment_number"):
            vals["apartment_number"] = location["apartment_number"]

        if location.get("latitude") is not None:
            vals["latitude"] = float(location["latitude"])

        if location.get("longitude") is not None:
            vals["longitude"] = float(location["longitude"])

    @api.model
    def _generate_name_from_vals(self, vals):
        parts = []
        property_type_labels = {
            "apartment": "Квартира",
            "house": "Дом",
            "townhouse": "Таунхаус",
            "commercial": "Коммерция",
            "land": "Земля",
        }
        label = property_type_labels.get(vals.get("property_type"), "Объект")
        parts.append(label)

        if vals.get("area_total"):
            parts.append(f"{vals['area_total']} м²")

        if vals.get("price"):
            parts.append(f"{vals['price']:,.0f}")

        return " — ".join(parts) if len(parts) > 1 else parts[0]
