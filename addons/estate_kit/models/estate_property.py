import logging

from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError

from ..services.api_client import EstateKitApiClient
from ..services.image_sync_service import ImageSyncService
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

    @api.model_create_multi
    def create(self, vals_list):
        if not self.env.context.get("skip_duplicate_check"):
            from ..services.duplicate_checker import DuplicateChecker
            checker = DuplicateChecker(self.env)
            for vals in vals_list:
                # RPC-вызовы обязаны передавать адрес
                if not self.env.context.get("allow_empty_address"):
                    self._require_address_fields(vals)
                result = checker.check(vals)
                if result:
                    raise ValidationError(result.message)
        return super().create(vals_list)

    def write(self, vals):
        if not self.env.context.get("skip_duplicate_check"):
            from ..services.duplicate_checker import ADDRESS_FIELDS, DuplicateChecker
            if ADDRESS_FIELDS & set(vals):
                checker = DuplicateChecker(self.env)
                for record in self:
                    merged = {
                        "city_id": vals.get("city_id", record.city_id.id),
                        "street_id": vals.get("street_id", record.street_id.id),
                        "house_number": vals.get("house_number", record.house_number),
                        "apartment_number": vals.get("apartment_number", record.apartment_number),
                        "property_type": vals.get("property_type", record.property_type),
                        "deal_type": vals.get("deal_type", record.deal_type),
                    }
                    result = checker.check(merged, exclude_id=record.id)
                    if result:
                        raise ValidationError(result.message)
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

    @staticmethod
    def _require_address_fields(vals):
        """Проверяет наличие обязательных адресных полей (для RPC-вызовов)."""
        missing = []
        if not vals.get("city_id"):
            missing.append("city_id")
        if not vals.get("street_id"):
            missing.append("street_id")
        if not vals.get("house_number"):
            missing.append("house_number")
        if vals.get("property_type") == "apartment" and not vals.get("apartment_number"):
            missing.append("apartment_number")
        if missing:
            raise ValidationError(
                f"Для создания объекта обязательны адресные поля: {', '.join(missing)}"
            )

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

    def action_score_property(self):
        self.ensure_one()
        scoring = self.env["estate.property.scoring"].score_property(self.id)
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "message": (
                    f"AI-скоринг рассчитан: цена {scoring.price_score}/10, "
                    f"качество {scoring.quality_score}/10, "
                    f"маркетинг {scoring.marketing_score}/10"
                ),
                "type": "success",
                "sticky": False,
            },
        }

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
    tag_ids = fields.Many2many(
        "estate.property.tag",
        string="Теги",
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

    # === Маркетинг ===
    placement_ids = fields.One2many(
        "estate.property.placement",
        "property_id",
        string="Размещения",
    )
    scoring_ids = fields.One2many(
        "estate.property.scoring",
        "property_id",
        string="AI-скоринг",
    )
    tier_ids = fields.One2many(
        "estate.property.tier",
        "property_id",
        string="Тир-лист",
    )
    in_my_tier_list = fields.Boolean(
        string="В моём тир-листе",
        compute="_compute_in_my_tier_list",
    )

    @api.depends("tier_ids", "tier_ids.user_id")
    def _compute_in_my_tier_list(self):
        uid = self.env.uid
        for rec in self:
            rec.in_my_tier_list = any(t.user_id.id == uid for t in rec.tier_ids)

    def _get_tier_role(self):
        """Определить роль текущего пользователя для тир-листа."""
        user = self.env.user
        if user.has_group("estate_kit.group_estate_team_lead"):
            return "team_lead"
        if user.has_group("estate_kit.group_estate_listing_agent"):
            return "listing_agent"
        return None

    def action_add_to_tier_list(self):
        """Добавить объект в тир-лист текущего пользователя."""
        self.ensure_one()
        role = self._get_tier_role()
        if not role:
            raise ValidationError("У вас нет роли для работы с тир-листом.")
        Tier = self.env["estate.property.tier"]
        existing = Tier.search([
            ("property_id", "=", self.id),
            ("user_id", "=", self.env.uid),
            ("role", "=", role),
        ], limit=1)
        if existing:
            raise ValidationError("Объект уже в вашем тир-листе.")
        # max проверка сработает через constrains на модели tier
        max_priority = Tier.search([
            ("user_id", "=", self.env.uid),
            ("role", "=", role),
        ], order="priority desc", limit=1)
        next_priority = (max_priority.priority + 1) if max_priority else 1
        Tier.create({
            "property_id": self.id,
            "user_id": self.env.uid,
            "role": role,
            "priority": next_priority,
        })

    def action_remove_from_tier_list(self):
        """Убрать объект из тир-листа текущего пользователя."""
        self.ensure_one()
        role = self._get_tier_role()
        if not role:
            raise ValidationError("У вас нет роли для работы с тир-листом.")
        Tier = self.env["estate.property.tier"]
        existing = Tier.search([
            ("property_id", "=", self.id),
            ("user_id", "=", self.env.uid),
            ("role", "=", role),
        ], limit=1)
        if not existing:
            raise ValidationError("Объект не в вашем тир-листе.")
        # Проверка минимума
        _min, _max = existing._get_role_limits(role)
        count = Tier.search_count([
            ("user_id", "=", self.env.uid),
            ("role", "=", role),
        ])
        if count <= _min:
            raise ValidationError(
                f"Нельзя убрать — в тир-листе минимум {_min} объектов "
                f"для роли «{dict(Tier._fields['role'].selection)[role]}». "
                f"Сначала добавьте другой объект."
            )
        existing.unlink()

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
        ImageSyncService(self.env).push_images_for_property(self)

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

            from ..services.api_mapper.importer import API_DEAL_TYPE_MAP, API_PROPERTY_TYPE_MAP

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

    @api.model
    def _cron_create_callback_activities(self):
        """Create monthly callback activities for properties in marketing pool."""
        marketing_tag = self.env.ref(
            "estate_kit.property_tag_marketing_pool", raise_if_not_found=False
        )
        if not marketing_tag:
            _logger.warning("Marketing Pool tag not found, skipping callback cron")
            return

        properties = self.search([("tag_ids", "in", marketing_tag.ids)])
        if not properties:
            return

        activity_type = self.env.ref("mail.mail_activity_data_todo")
        model_id = self.env["ir.model"]._get_id("estate.property")
        note = (
            "<ul>"
            "<li>Объект ещё в продаже?</li>"
            "<li>Изменилась ли цена?</li>"
            "<li>Есть ли обновления по объекту?</li>"
            "</ul>"
        )

        for prop in properties:
            responsible_user = prop.user_id or prop.listing_agent_id
            if not responsible_user:
                continue
            self.env["mail.activity"].create({
                "activity_type_id": activity_type.id,
                "summary": "Обзвон: проверка актуальности",
                "note": note,
                "res_model_id": model_id,
                "res_id": prop.id,
                "user_id": responsible_user.id,
            })

        _logger.info(
            "Callback activities created for %d properties in marketing pool",
            len(properties),
        )

    # === Cron: ротация маркетингового пула ===

    POOL_INACTIVE_STATES = ("sold", "unpublished", "archived", "mls_sold", "mls_removed")

    @api.model
    def _cron_rotate_pool(self):
        """Weekly rotation of the marketing pool based on scoring and property state."""
        pool_tag = self.env.ref(
            "estate_kit.property_tag_marketing_pool", raise_if_not_found=False
        )
        if not pool_tag:
            _logger.warning("Marketing pool tag not found, skipping rotation.")
            return

        min_score = int(
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("estate_kit.pool_min_score", "5")
        )

        pool_properties = self.search([("tag_ids", "in", pool_tag.id)])

        for prop in pool_properties:
            if prop.state in self.POOL_INACTIVE_STATES:
                self._pool_remove(prop, pool_tag, "Объект в статусе «%s»" % prop.state)
                continue

            latest_scoring = prop.scoring_ids[:1]
            if latest_scoring:
                avg_score = (
                    latest_scoring.price_score
                    + latest_scoring.quality_score
                    + latest_scoring.marketing_score
                ) / 3.0
                if avg_score < min_score:
                    self._pool_remove(
                        prop,
                        pool_tag,
                        "Средний скоринг %.1f ниже порога %d" % (avg_score, min_score),
                    )

        self._pool_suggest_candidates(pool_tag, min_score)

    def _pool_remove(self, prop, pool_tag, reason):
        """Remove property from marketing pool and set active placements to removed."""
        prop.tag_ids -= pool_tag
        active_placements = prop.placement_ids.filtered(
            lambda p: p.state in ("draft", "active", "paused")
        )
        if active_placements:
            active_placements.write({"state": "removed"})
        prop.message_post(
            body="Выведен из маркетингового пула: %s" % reason,
            message_type="comment",
            subtype_xmlid="mail.mt_note",
        )
        _logger.info("Property %s removed from pool: %s", prop.id, reason)

    @api.model
    def _pool_suggest_candidates(self, pool_tag, min_score):
        """Find high-scoring properties not in pool and notify via activity."""
        Scoring = self.env["estate.property.scoring"]
        recent_scorings = Scoring.search([], order="scored_at desc")

        seen_property_ids = set()
        candidates = self.env["estate.property"]
        for scoring in recent_scorings:
            pid = scoring.property_id.id
            if pid in seen_property_ids:
                continue
            seen_property_ids.add(pid)
            avg = (
                scoring.price_score + scoring.quality_score + scoring.marketing_score
            ) / 3.0
            if avg >= min_score * 1.5:
                prop = scoring.property_id
                if (
                    pool_tag not in prop.tag_ids
                    and prop.state not in self.POOL_INACTIVE_STATES
                ):
                    candidates |= prop

        for prop in candidates:
            latest = prop.scoring_ids[:1]
            avg = (
                latest.price_score + latest.quality_score + latest.marketing_score
            ) / 3.0
            prop.activity_schedule(
                act_type_xmlid="mail.mail_activity_data_todo",
                summary="Кандидат в маркетинговый пул",
                note="Средний скоринг: %.1f. Рассмотрите включение в пул." % avg,
            )
            _logger.info(
                "Property %s suggested for pool (avg score: %.1f)", prop.id, avg
            )

