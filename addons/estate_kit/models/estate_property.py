import logging

from odoo import api, fields, models
from odoo.exceptions import UserError

from ..services.api_client import EstateKitApiClient
from ..services.api_mapper import prepare_api_payload
from ..services.api_mapper.property_types import API_PROPERTY_TYPE_MAP, PROPERTY_TYPE_LABELS

_logger = logging.getLogger(__name__)

API_DEAL_TYPE_MAP = {
    1: "sale",
    2: "rent_long",
    3: "rent_daily",
}

API_STATE_MAP = {
    1: "draft",
    2: "internal_review",
    3: "active",
    4: "moderation",
    5: "legal_review",
    6: "published",
    7: "rejected",
    8: "unpublished",
    9: "sold",
    10: "archived",
    11: "mls_listed",
    12: "mls_removed",
    13: "mls_sold",
}

ALLOWED_TRANSITIONS = {
    "draft": ["internal_review"],
    "internal_review": ["draft", "active"],
    "active": ["moderation", "sold", "unpublished"],
    "moderation": ["legal_review", "rejected", "active"],
    "legal_review": ["published", "rejected", "moderation", "active"],
    "published": ["unpublished", "sold", "archived", "active"],
    "rejected": ["internal_review"],
    "unpublished": ["active"],
    "archived": [],
    "sold": [],
    "mls_listed": ["mls_removed", "mls_sold"],
    "mls_removed": [],
    "mls_sold": [],
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
            ("draft", "Черновик"),
            ("internal_review", "Внутренняя проверка"),
            ("active", "В продаже"),
            ("moderation", "На модерации MLS"),
            ("legal_review", "Юридическая проверка"),
            ("published", "Опубликован в MLS"),
            ("rejected", "Отклонён MLS"),
            ("unpublished", "Снят с публикации"),
            ("sold", "Продан"),
            ("archived", "Архив"),
            ("mls_listed", "В MLS (чужой)"),
            ("mls_removed", "Удалён из MLS"),
            ("mls_sold", "Продан (чужой)"),
        ],
        string="Стадия",
        required=True,
        copy=False,
        default="draft",
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
    residential_complex = fields.Char(string="Жилой комплекс")

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
            if not self.env.context.get("force_state_change"):
                for record in self:
                    allowed = ALLOWED_TRANSITIONS.get(record.state, [])
                    if new_state not in allowed:
                        raise UserError(
                            f"Переход из «{record.state}» в «{new_state}» не разрешён. "
                            "Используйте соответствующую кнопку действия."
                        )
        result = super().write(vals)
        return result

    def _transition_state(self, from_states, to_state, error_msg):
        if isinstance(from_states, str):
            from_states = (from_states,)
        for record in self:
            if record.state not in from_states:
                raise UserError(error_msg)
        self.with_context(force_state_change=True).write({"state": to_state})

    def action_submit_review(self):
        self._transition_state("draft", "internal_review", "Отправить на проверку можно только черновик.")

    def action_return_draft(self):
        self._transition_state("internal_review", "draft", "Вернуть в черновик можно только из внутренней проверки.")

    def action_approve(self):
        self._transition_state("internal_review", "active", "Одобрить можно только объект на внутренней проверке.")

    def action_send_to_mls(self):
        self._transition_state("active", "moderation", "Отправить в MLS можно только объект в продаже.")
        for record in self:
            record._push_to_api()

    def action_remove_from_mls(self):
        self._transition_state(
            ("moderation", "legal_review", "published"), "active",
            "Убрать из MLS возможен только для объектов в MLS-процессе.",
        )

    def action_sell(self):
        self._transition_state(
            ("active", "published"), "sold",
            "Отметить как проданный можно только объект в продаже или опубликованный.",
        )

    def action_unpublish(self):
        self._transition_state(
            ("active", "published"), "unpublished",
            "Снять можно только объект в продаже или опубликованный.",
        )
        for record in self:
            if record.external_id:
                client = EstateKitApiClient(record.env)
                if client._is_configured:
                    try:
                        client.post(f"/properties/{record.external_id}/suspend")
                    except Exception:
                        _logger.exception(
                            "Failed to suspend property %s (external_id=%s) via API",
                            record.name, record.external_id,
                        )

    def action_republish(self):
        self._transition_state("unpublished", "active", "Вернуть в продажу можно только снятый с публикации объект.")
        for record in self:
            if record.external_id:
                client = EstateKitApiClient(record.env)
                if client._is_configured:
                    try:
                        client.post(f"/properties/{record.external_id}/resume")
                    except Exception:
                        _logger.exception(
                            "Failed to resume property %s (external_id=%s) via API",
                            record.name, record.external_id,
                        )

    def action_archive_property(self):
        self._transition_state("published", "archived", "Архивировать можно только опубликованный объект.")

    def action_fix_rejected(self):
        self._transition_state("rejected", "internal_review", "Исправить можно только отклонённый объект.")

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
        from ..services.geocoder import geocode_address, reverse_geocode_district

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

        coords = geocode_address(api_key, address)
        if not coords:
            raise UserError(f"Адрес не найден: {address}")

        lat, lon = coords

        if not self.latitude or not self.longitude:
            self.latitude = lat
            self.longitude = lon

        district_name = reverse_geocode_district(api_key, lat, lon)

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

    # === MLS ===
    is_locked_by_other_agency = fields.Boolean(
        string="Заблокирован другим агентством",
        default=False,
        copy=False,
    )

    # === Медиа ===
    image_ids = fields.One2many(
        "estate.property.image",
        "property_id",
        string="Фотографии",
    )

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
            raise UserError(
                "API не настроен. Укажите API URL и API Key в "
                "Настройки → Технические → Параметры системы "
                "(estate_kit.api_url и estate_kit.api_key)."
            )

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
                    owner_data = response.get("owner")
                    if (
                        owner_data
                        and owner_data.get("created")
                        and owner_data.get("id")
                        and self.owner_id
                    ):
                        self.owner_id.write(
                            {"external_owner_id": owner_data["id"]}
                        )
        except Exception:
            _logger.exception(
                "Failed to push property %s (id=%s) to API", self.name, self.id
            )
            raise UserError(
                "Не удалось отправить объект в MLS. API вернул ошибку. "
                "Попробуйте позже или обратитесь к администратору."
            )

    def _prepare_api_payload(self):
        self.ensure_one()
        return prepare_api_payload(self)

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
    def _find_property_for_webhook(self, payload, event_name):
        property_id = payload.get("data", {}).get("property_id")
        if not property_id:
            _logger.warning("%s: missing property_id in payload", event_name)
            return None, None
        existing = self.search([("external_id", "=", property_id)], limit=1)
        if not existing:
            _logger.warning(
                "%s: property with external_id=%s not found", event_name, property_id
            )
        return property_id, existing

    @api.model
    def _handle_webhook_property_transition(self, payload):
        data = payload.get("data", {})
        status_id = data.get("status_id")
        property_id, existing = self._find_property_for_webhook(
            payload, "property.transition"
        )
        if not property_id:
            return

        new_state = API_STATE_MAP.get(status_id)
        if not new_state:
            _logger.warning(
                "property.transition: unknown status_id=%s for property %d",
                status_id,
                property_id,
            )
            return

        if not existing:
            return

        existing.with_context(
            skip_api_sync=True, force_state_change=True
        ).write({"state": new_state})
        _logger.info(
            "property.transition: property %d state → %s", property_id, new_state
        )

    @api.model
    def _handle_webhook_contact_request(self, payload):
        property_id, prop = self._find_property_for_webhook(
            payload, "contact_request.received"
        )
        if not property_id or not prop:
            return

        responsible_user = prop.user_id or prop.listing_agent_id
        if not responsible_user:
            _logger.warning(
                "contact_request.received: no responsible user for property id=%s",
                prop.id,
            )
            return

        data = payload.get("data", {})
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
        vals["state"] = "mls_listed"
        self.with_context(skip_api_sync=True, force_state_change=True).create(vals)
        _logger.info("mls.new_listing: created property with external_id=%d", property_id)

    @api.model
    def _handle_webhook_mls_listing_removed(self, payload):
        property_id, existing = self._find_property_for_webhook(
            payload, "mls.listing_removed"
        )
        if not property_id or not existing:
            return
        existing.with_context(skip_api_sync=True, force_state_change=True).write({"state": "mls_removed"})
        _logger.info("mls.listing_removed: set mls_removed for property with external_id=%d", property_id)

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

        city_name = location.get("city_name") or location.get("city")
        if city_name:
            city = self.env["estate.city"].search(
                [("name", "=", city_name)], limit=1
            )
            if city:
                vals["city_id"] = city.id
            else:
                _logger.warning("City '%s' not found, skipping", city_name)

        district_name = location.get("district_name") or location.get("district")
        if district_name:
            district = self.env["estate.district"].search(
                [("name", "=", district_name)], limit=1
            )
            if district:
                vals["district_id"] = district.id
            else:
                _logger.warning("District '%s' not found, skipping", district_name)

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

        if location.get("residential_complex"):
            vals["residential_complex"] = location["residential_complex"]

        if location.get("apartment_number"):
            vals["apartment_number"] = location["apartment_number"]

        if location.get("latitude") is not None:
            vals["latitude"] = float(location["latitude"])

        if location.get("longitude") is not None:
            vals["longitude"] = float(location["longitude"])

    @api.model
    def _generate_name_from_vals(self, vals):
        parts = []
        label = PROPERTY_TYPE_LABELS.get(vals.get("property_type"), "Объект")
        parts.append(label)

        if vals.get("area_total"):
            parts.append(f"{vals['area_total']} м²")

        if vals.get("price"):
            parts.append(f"{vals['price']:,.0f}")

        return " — ".join(parts) if len(parts) > 1 else parts[0]
