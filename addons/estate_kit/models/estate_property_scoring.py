import logging

from odoo import api, fields, models
from odoo.exceptions import UserError

from ..services.anthropic_client import AnthropicClient

_logger = logging.getLogger(__name__)

PROPERTY_TYPE_LABELS = {
    "apartment": "Квартира",
    "house": "Дом",
    "townhouse": "Таунхаус",
    "commercial": "Коммерция",
    "land": "Земля",
}

DEAL_TYPE_LABELS = {
    "sale": "Продажа",
    "rent_long": "Долгосрочная аренда",
    "rent_daily": "Посуточная аренда",
}

CONDITION_LABELS = {
    "no_repair": "Без ремонта",
    "cosmetic": "Косметический",
    "euro": "Евроремонт",
    "designer": "Дизайнерский",
}


class EstatePropertyScoring(models.Model):
    _name = "estate.property.scoring"
    _description = "AI-скоринг объекта"
    _order = "scored_at desc"

    property_id = fields.Many2one(
        "estate.property",
        string="Объект",
        required=True,
        ondelete="cascade",
        index=True,
    )
    price_score = fields.Integer(string="Цена (балл)")
    quality_score = fields.Integer(string="Качество (балл)")
    listing_score = fields.Integer(string="Карточка (балл)")
    price_score_color = fields.Char(
        string="Цена", compute="_compute_score_color",
    )
    quality_score_color = fields.Char(
        string="Качество", compute="_compute_score_color",
    )
    listing_score_color = fields.Char(
        string="Карточка", compute="_compute_score_color",
    )
    rationale = fields.Text(string="Обоснование")
    scored_at = fields.Datetime(string="Дата оценки", default=fields.Datetime.now)

    @api.depends("price_score", "quality_score", "listing_score")
    def _compute_score_color(self):
        for rec in self:
            rec.price_score_color = self._score_to_color(rec.price_score)
            rec.quality_score_color = self._score_to_color(rec.quality_score)
            rec.listing_score_color = self._score_to_color(rec.listing_score)

    @staticmethod
    def _score_to_color(score):
        """Return score with color emoji: red (1-3), yellow (4-6), green (7-10)."""
        if score <= 3:
            return f"🔴 {score}/10"
        if score <= 6:
            return f"🟡 {score}/10"
        return f"🟢 {score}/10"

    @api.model
    def score_property(self, property_id):
        prop = self.env["estate.property"].browse(property_id)
        if not prop.exists():
            raise UserError("Объект не найден.")

        client = AnthropicClient(self.env)
        if not client.is_configured:
            raise UserError(
                "API-ключ Anthropic не настроен. "
                "Перейдите в Настройки → Estate Kit → AI-скоринг."
            )

        Log = self.env["estate.kit.log"]
        CAT = "ai_scoring"

        property_data = self._collect_property_data(prop)
        # Build details from the actual user message sent to AI
        detail_parts = [
            "model=%s" % client.model,
            "промпт=%s" % prop.property_type,
        ]
        from ..services.anthropic_client import _COMMON_FIELDS, PROPERTY_TYPE_FIELDS
        all_fields = _COMMON_FIELDS + PROPERTY_TYPE_FIELDS.get(prop.property_type, [])
        for key, label, _optional in all_fields:
            value = property_data.get(key)
            if value:
                detail_parts.append("%s=%s" % (label, value))
        Log.log(
            CAT,
            "Запрос AI-скоринга: %s [%s]" % (prop.name, prop.property_type),
            details=", ".join(detail_parts),
            property_id=prop.id,
        )
        self.env.cr.commit()

        result = client.score_property(property_data)
        if result is None:
            Log.log(
                CAT,
                "Ошибка AI-скоринга: %s" % prop.name,
                level="error",
                property_id=prop.id,
            )
            self.env.cr.commit()
            raise UserError(
                "Не удалось получить оценку от AI. Проверьте логи сервера."
            )

        scoring = self.create({
            "property_id": prop.id,
            "price_score": result["price_score"],
            "quality_score": result["quality_score"],
            "listing_score": result["listing_score"],
            "rationale": result["rationale"],
        })
        Log.log(
            CAT,
            "Ответ AI-скоринга: %s → price=%d, quality=%d, listing=%d"
            % (prop.name, scoring.price_score, scoring.quality_score, scoring.listing_score),
            details=result.get("rationale", ""),
            property_id=prop.id,
        )
        self.env.cr.commit()

        _logger.info(
            "AI scoring created for property %s: price=%s quality=%s listing=%s",
            prop.id,
            scoring.price_score,
            scoring.quality_score,
            scoring.listing_score,
        )
        return scoring

    def _collect_property_data(self, prop):
        price_per_sqm = 0
        if prop.price and prop.area_total:
            price_per_sqm = round(prop.price / prop.area_total)

        # Selection fields: resolve to human-readable labels
        selection_labels = {
            "property_type": PROPERTY_TYPE_LABELS,
            "deal_type": DEAL_TYPE_LABELS,
            "condition": CONDITION_LABELS,
            "building_type": {"panel": "Панельный", "brick": "Кирпичный", "monolith": "Монолит",
                              "metal_frame": "Металлокаркас", "wood": "Деревянный"},
            "wall_material": {"brick": "Кирпич", "gas_block": "Газоблок", "wood": "Дерево",
                              "sip": "СИП-панели", "frame": "Каркас", "polystyrene": "Полистиролбетон"},
            "roof_type": {"flat": "Плоская", "gable": "Двускатная", "hip": "Вальмовая"},
            "foundation": {"strip": "Ленточный", "slab": "Плитный", "pile": "Свайный"},
            "bathroom": {"combined": "Совмещённый", "separate": "Раздельный"},
            "balcony": {"none": "Нет", "balcony": "Балкон", "loggia": "Лоджия", "terrace": "Терраса"},
            "parking": {"none": "Нет", "yard": "Двор", "underground": "Подземная",
                        "garage": "Гараж", "ground": "Наземная"},
            "furniture": {"none": "Без мебели", "partial": "Частично", "full": "Полная"},
            "heating": {"central": "Центральное", "autonomous": "Автономное", "none": "Нет"},
            "water": {"central": "Центральное", "well": "Скважина", "none": "Нет"},
            "sewage": {"central": "Центральная", "septic": "Септик", "none": "Нет"},
            "gas": {"central": "Центральный", "balloon": "Баллонный", "none": "Нет"},
            "electricity": {"yes": "Есть", "nearby": "Рядом", "none": "Нет"},
            "commercial_type": {"office": "Офис", "retail": "Торговое", "warehouse": "Склад",
                                "production": "Производство"},
            "land_category": {"izhs": "ИЖС", "snt": "СНТ", "lpkh": "ЛПХ", "commercial": "Коммерческое"},
            "land_status": {"owned": "В собственности", "leased": "Аренда"},
            "road_access": {"asphalt": "Асфальт", "gravel": "Гравий", "dirt": "Грунтовая", "none": "Нет"},
        }

        def get_value(field_name: str):
            raw = getattr(prop, field_name, None)
            if raw is None:
                return None
            if field_name in selection_labels:
                return selection_labels[field_name].get(raw, raw) if raw else None
            # Many2one fields
            if hasattr(raw, 'name'):
                return raw.name if raw else None
            # Boolean — return only if True
            if isinstance(raw, bool):
                return "Да" if raw else None
            return raw or None

        data = {
            "property_type": get_value("property_type"),
            "deal_type": get_value("deal_type"),
            "price": prop.price,
            "price_per_sqm": price_per_sqm,
            "currency": prop.currency_id.name if prop.currency_id else "",
            "area_total": prop.area_total,
            "city": prop.city_id.name if prop.city_id else "",
            "district": prop.district_id.name if prop.district_id else "",
            "description": (prop.description or "")[:1000],
            "photo_count": len(prop.image_ids),
            # Type-specific fields collected dynamically
            "rooms": get_value("rooms"),
            "bedrooms": get_value("bedrooms"),
            "floor": get_value("floor"),
            "floors_total": get_value("floors_total"),
            "year_built": get_value("year_built"),
            "building_type": get_value("building_type"),
            "ceiling_height": get_value("ceiling_height"),
            "condition": get_value("condition"),
            "area_living": get_value("area_living"),
            "area_kitchen": get_value("area_kitchen"),
            "area_land": get_value("area_land"),
            "area_commercial": get_value("area_commercial"),
            "area_warehouse": get_value("area_warehouse"),
            "wall_material": get_value("wall_material"),
            "roof_type": get_value("roof_type"),
            "foundation": get_value("foundation"),
            "bathroom": get_value("bathroom"),
            "balcony": get_value("balcony"),
            "parking": get_value("parking"),
            "furniture": get_value("furniture"),
            "heating": get_value("heating"),
            "water": get_value("water"),
            "sewage": get_value("sewage"),
            "gas": get_value("gas"),
            "electricity": get_value("electricity"),
            "internet": get_value("internet"),
            "residential_complex": prop.residential_complex or "",
            "commercial_type": get_value("commercial_type"),
            "separate_entrance": get_value("separate_entrance"),
            "has_showcase": get_value("has_showcase"),
            "electricity_power": get_value("electricity_power"),
            "communications_nearby": get_value("communications_nearby"),
            "land_category": get_value("land_category"),
            "land_status": get_value("land_status"),
            "road_access": get_value("road_access"),
        }
        return data
