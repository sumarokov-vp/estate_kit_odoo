import logging

from odoo import api, fields, models
from odoo.exceptions import UserError

from ..services.api_client import EstateKitApiClient
from ..services.property_sync_service import PropertySyncService

_logger = logging.getLogger(__name__)

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
    _inherit = ["mail.thread", "mail.activity.mixin", "estate.property.webhook.mixin"]
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

    def _api_call_action(self, action: str):
        for record in self:
            if record.external_id:
                client = EstateKitApiClient(record.env)
                if client.is_configured:
                    client.post(f"/properties/{record.external_id}/{action}", {})

    def _api_resume(self):
        self._api_call_action("resume")

    def _api_suspend(self):
        self._api_call_action("suspend")

    def action_send_to_mls(self):
        self._transition_state("active", "moderation", "Отправить в MLS можно только объект в продаже.")
        for record in self:
            if record.external_id:
                record._api_resume()
            else:
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
        self._api_suspend()

    def action_republish(self):
        self._transition_state("unpublished", "active", "Вернуть в продажу можно только снятый с публикации объект.")
        self._api_resume()

    def action_archive_property(self):
        self._transition_state("published", "archived", "Архивировать можно только опубликованный объект.")

    def action_fix_rejected(self):
        self._transition_state("rejected", "internal_review", "Исправить можно только отклонённый объект.")

    def _build_address_parts(self, include_district=True):
        self.ensure_one()
        parts = []
        if self.city_id:
            parts.append(self.city_id.name)
        if include_district and self.district_id:
            parts.append(self.district_id.name)
        if self.street_id:
            parts.append(self.street_id.name)
        if self.house_number:
            parts.append(self.house_number)
        return parts

    @api.depends("city_id", "district_id", "street_id", "house_number")
    def _compute_geo_address(self):
        for record in self:
            parts = record._build_address_parts(include_district=True)
            record.geo_address = ", ".join(parts) if parts else False

    @api.model
    def _default_city(self):
        code = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("estate_kit.default_city_code", "almaty")
        )
        return self.env["estate.city"].search([("code", "=", code)], limit=1)

    @api.onchange("city_id")
    def _onchange_city_id(self):
        if self.district_id and self.district_id.city_id != self.city_id:
            self.district_id = False
        if self.street_id and self.street_id.city_id != self.city_id:
            self.street_id = False

    def action_detect_district(self):
        from ..services.geocoder import YandexGeocoder

        self.ensure_one()
        geocoder = YandexGeocoder(self.env)
        if not geocoder.is_configured:
            raise UserError("API ключ Yandex Geocoder не настроен")

        address_parts = self._build_address_parts(include_district=False)
        if not address_parts:
            raise UserError("Укажите адрес для определения района")

        coords = geocoder.geocode_address(", ".join(address_parts))
        if not coords:
            raise UserError(f"Адрес не найден: {', '.join(address_parts)}")

        lat, lon = coords
        if not self.latitude or not self.longitude:
            self.latitude = lat
            self.longitude = lon

        if self.city_id:
            district = geocoder.find_or_create_district(self.env, lat, lon, self.city_id.id)
            if district:
                self.district_id = district.id

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
    mls_rejection_reason = fields.Text(string="Причина отклонения MLS", copy=False)
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
        return PropertySyncService(self.env).push_owner(self)

    def _push_to_api(self):
        self.ensure_one()
        PropertySyncService(self.env).push_property(self)

    # === Unified Search (XML-RPC) ===

    # Reverse maps: Odoo selection value -> API integer ID
    _PROPERTY_TYPE_TO_API_ID = {v: k for k, v in {
        1: "apartment", 2: "house", 3: "townhouse", 4: "commercial", 5: "land",
    }.items()}
    _DEAL_TYPE_TO_API_ID = {v: k for k, v in {
        1: "sale", 2: "rent_long", 3: "rent_daily",
    }.items()}

    @api.model
    def search_unified(self, criteria, limit=50, offset=0, count=False):
        """Search local + MLS properties, return unified list of dicts.

        Accessible via XML-RPC. Deduplicates by external_id / MLS id.
        If count=True, returns total count instead of results.
        If MLS is unavailable, returns only local results.
        """
        criteria = criteria or {}
        local_results = self._search_unified_local(criteria, limit, offset)
        mls_results = self._search_unified_mls(criteria, limit, offset)

        # Deduplicate: local wins over MLS if same external_id
        local_mls_ids = {r["mls_id"] for r in local_results if r.get("mls_id")}
        merged = list(local_results)
        for item in mls_results:
            if item.get("mls_id") and item["mls_id"] not in local_mls_ids:
                merged.append(item)

        if count:
            return len(merged)

        return merged[:limit]

    def _search_unified_local(self, criteria, limit, offset):
        domain = [("active", "=", True)]

        if criteria.get("deal_type"):
            domain.append(("deal_type", "=", criteria["deal_type"]))
        if criteria.get("property_type"):
            domain.append(("property_type", "=", criteria["property_type"]))
        if criteria.get("city_id"):
            domain.append(("city_id", "=", criteria["city_id"]))
        if criteria.get("district_id"):
            domain.append(("district_id", "=", criteria["district_id"]))
        if criteria.get("rooms"):
            domain.append(("rooms", "=", criteria["rooms"]))
        if criteria.get("min_price"):
            domain.append(("price", ">=", criteria["min_price"]))
        if criteria.get("max_price"):
            domain.append(("price", "<=", criteria["max_price"]))
        if criteria.get("min_area"):
            domain.append(("area_total", ">=", criteria["min_area"]))
        if criteria.get("max_area"):
            domain.append(("area_total", "<=", criteria["max_area"]))
        if criteria.get("floor_min"):
            domain.append(("floor", ">=", criteria["floor_min"]))
        if criteria.get("floor_max"):
            domain.append(("floor", "<=", criteria["floor_max"]))

        records = self.search_read(
            domain,
            fields=[
                "id", "external_id", "property_type", "deal_type",
                "city_id", "district_id", "street_id", "house_number",
                "rooms", "area_total", "floor", "floors_total",
                "price", "description", "create_date",
            ],
            limit=limit,
            offset=offset,
            order="create_date desc",
        )

        results = []
        for rec in records:
            city_name = rec["city_id"][1] if rec.get("city_id") else ""
            district_name = rec["district_id"][1] if rec.get("district_id") else ""
            street_name = rec["street_id"][1] if rec.get("street_id") else ""
            address_parts = [p for p in [city_name, district_name, street_name, rec.get("house_number") or ""] if p]

            # Collect photo URLs
            photo_urls = []
            thumbnail_url = ""
            images = self.env["estate.property.image"].search_read(
                [("property_id", "=", rec["id"])],
                fields=["image_url"],
                limit=10,
            )
            for img in images:
                if img.get("image_url"):
                    photo_urls.append(img["image_url"])
            if photo_urls:
                thumbnail_url = photo_urls[0]

            results.append({
                "id": rec["id"],
                "source": "local",
                "mls_id": rec.get("external_id") or 0,
                "property_type": rec.get("property_type") or "",
                "deal_type": rec.get("deal_type") or "",
                "city": city_name,
                "district": district_name,
                "address": ", ".join(address_parts),
                "rooms": rec.get("rooms") or 0,
                "area": rec.get("area_total") or 0.0,
                "floor": rec.get("floor") or 0,
                "total_floors": rec.get("floors_total") or 0,
                "price": rec.get("price") or 0.0,
                "description": rec.get("description") or "",
                "thumbnail_url": thumbnail_url,
                "photo_urls": photo_urls,
                "created_at": rec.get("create_date") or "",
            })

        return results

    def _search_unified_mls(self, criteria, limit, offset):
        client = EstateKitApiClient(self.env)
        if not client.is_configured:
            return []

        params = {"limit": limit, "offset": offset}
        if criteria.get("property_type"):
            api_id = self._PROPERTY_TYPE_TO_API_ID.get(criteria["property_type"])
            if api_id:
                params["property_type_id"] = api_id
        if criteria.get("deal_type"):
            api_id = self._DEAL_TYPE_TO_API_ID.get(criteria["deal_type"])
            if api_id:
                params["deal_type_id"] = api_id
        if criteria.get("city_id"):
            params["city_id"] = criteria["city_id"]
        if criteria.get("min_price"):
            params["min_price"] = criteria["min_price"]
        if criteria.get("max_price"):
            params["max_price"] = criteria["max_price"]

        try:
            data = client.get("/mls/properties", params=params)
        except Exception:
            _logger.warning("MLS API unavailable, returning empty MLS results", exc_info=True)
            return []

        if not data or not isinstance(data, dict):
            return []

        items = data.get("items", [])
        results = []
        for item in items:
            prop_type_obj = item.get("property_type") or {}
            deal_type_obj = item.get("deal_type") or {}
            city_obj = item.get("city") or {}
            district_obj = item.get("district") or {}

            from ..services.api_mapper.importer import API_PROPERTY_TYPE_MAP, API_DEAL_TYPE_MAP

            results.append({
                "id": item.get("id", 0),
                "source": "mls",
                "mls_id": item.get("id", 0),
                "property_type": API_PROPERTY_TYPE_MAP.get(prop_type_obj.get("id"), ""),
                "deal_type": API_DEAL_TYPE_MAP.get(deal_type_obj.get("id"), ""),
                "city": city_obj.get("name", ""),
                "district": district_obj.get("name", ""),
                "address": "",
                "rooms": item.get("rooms") or 0,
                "area": item.get("area") or 0.0,
                "floor": item.get("floor") or 0,
                "total_floors": item.get("total_floors") or 0,
                "price": item.get("price") or 0.0,
                "description": "",
                "thumbnail_url": item.get("thumbnail_url") or "",
                "photo_urls": [],
                "created_at": item.get("created_at") or "",
            })

        return results

