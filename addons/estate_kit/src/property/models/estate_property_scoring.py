from odoo import api, fields, models

from ..services.ai_scoring import Factory as AiScoringFactory
from ..services.ai_scoring.score_colorizer import ScoreColorizer

_score_colorizer = ScoreColorizer()


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
            rec.price_score_color = _score_colorizer.colorize(rec.price_score)
            rec.quality_score_color = _score_colorizer.colorize(rec.quality_score)
            rec.listing_score_color = _score_colorizer.colorize(rec.listing_score)

    @api.model
    def score_property(self, property_id: int):
        return AiScoringFactory.create(self.env).score(property_id)
