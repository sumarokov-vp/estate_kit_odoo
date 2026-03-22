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
    price_score = fields.Integer(string="Оценка цены (1-10)")
    quality_score = fields.Integer(string="Оценка качества (1-10)")
    marketing_score = fields.Integer(string="Маркетинговый балл (1-10)")
    rationale = fields.Text(string="Обоснование")
    scored_at = fields.Datetime(string="Дата оценки", default=fields.Datetime.now)

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

        property_data = self._collect_property_data(prop)
        result = client.score_property(property_data)
        if result is None:
            raise UserError(
                "Не удалось получить оценку от AI. Проверьте логи сервера."
            )

        scoring = self.create({
            "property_id": prop.id,
            "price_score": result["price_score"],
            "quality_score": result["quality_score"],
            "marketing_score": result["marketing_score"],
            "rationale": result["rationale"],
        })
        _logger.info(
            "AI scoring created for property %s: price=%s quality=%s marketing=%s",
            prop.id,
            scoring.price_score,
            scoring.quality_score,
            scoring.marketing_score,
        )
        return scoring

    def _collect_property_data(self, prop):
        return {
            "property_type": PROPERTY_TYPE_LABELS.get(prop.property_type, prop.property_type),
            "deal_type": DEAL_TYPE_LABELS.get(prop.deal_type, prop.deal_type),
            "price": prop.price,
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
