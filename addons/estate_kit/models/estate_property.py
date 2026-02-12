import logging
import requests

from odoo import api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


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
        return super().write(vals)

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

    # === Медиа ===
    image_ids = fields.One2many(
        "estate.property.image",
        "property_id",
        string="Фотографии",
    )

    @api.model
    def get_twogis_api_key(self):
        return (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("estate_kit.twogis_api_key", "")
        )
