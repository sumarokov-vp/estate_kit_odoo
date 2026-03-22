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
        Log.log(
            CAT,
            "Запрос AI-скоринга: %s" % prop.name,
            details="model=%s, тип=%s, сделка=%s, цена=%s, площадь=%s м², "
                    "комнат=%s, этаж=%s, город=%s, район=%s, фото=%s"
                    % (
                        client.model,
                        property_data.get("property_type", "—"),
                        property_data.get("deal_type", "—"),
                        property_data.get("price", "—"),
                        property_data.get("area_total", "—"),
                        property_data.get("rooms", "—"),
                        property_data.get("floor", "—"),
                        property_data.get("city", "—"),
                        property_data.get("district", "—"),
                        property_data.get("photo_count", "—"),
                    ),
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
        return {
            "property_type": PROPERTY_TYPE_LABELS.get(prop.property_type, prop.property_type),
            "deal_type": DEAL_TYPE_LABELS.get(prop.deal_type, prop.deal_type),
            "price": prop.price,
            "price_per_sqm": price_per_sqm,
            "currency": prop.currency_id.name if prop.currency_id else "",
            "area_total": prop.area_total,
            "rooms": prop.rooms,
            "floor": prop.floor,
            "floors_total": prop.floors_total,
            "year_built": prop.year_built,
            "condition": CONDITION_LABELS.get(prop.condition, prop.condition or ""),
            "city": prop.city_id.name if prop.city_id else "",
            "district": prop.district_id.name if prop.district_id else "",
            "residential_complex": prop.residential_complex or "",
            "description": (prop.description or "")[:1000],
            "photo_count": len(prop.image_ids),
        }
