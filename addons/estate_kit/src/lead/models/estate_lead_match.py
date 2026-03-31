from odoo import fields, models

from ..services.lead_matcher import Factory as LeadMatcherFactory
from ..services.match_transition import Factory as MatchTransitionFactory


class EstateleadMatch(models.Model):
    _name = "estate.lead.match"
    _description = "Результат подбора"
    _order = "marketing_pool_score desc, match_date desc"

    lead_id = fields.Many2one(
        "crm.lead",
        string="Лид",
        required=True,
        ondelete="cascade",
        index=True,
    )
    property_id = fields.Many2one(
        "estate.property",
        string="Объект",
        required=True,
        ondelete="restrict",
    )
    property_price = fields.Monetary(
        related="property_id.price",
        string="Цена",
    )
    currency_id = fields.Many2one(
        related="property_id.currency_id",
    )
    score = fields.Float(string="Совпадение")
    match_date = fields.Datetime(string="Дата подбора", default=fields.Datetime.now)
    viewed_date = fields.Datetime(string="Дата просмотра", readonly=True)
    marketing_pool_score = fields.Float(
        related="property_id.marketing_pool_score",
        string="MPS (число)",
        store=True,
    )
    marketing_pool_score_display = fields.Char(
        related="property_id.marketing_pool_score_display",
        string="MPS",
    )
    price_score = fields.Integer(
        related="property_id.scoring_ids.price_score",
        string="Цена (балл)",
    )
    quality_score = fields.Integer(
        related="property_id.scoring_ids.quality_score",
        string="Качество (балл)",
    )
    listing_score = fields.Integer(
        related="property_id.scoring_ids.listing_score",
        string="Карточка (балл)",
    )
    stage_id = fields.Many2one(
        "estate.lead.match.stage",
        string="Стадия",
        default=lambda self: self.env.ref(
            "estate_kit.match_stage_new", raise_if_not_found=False
        ),
        group_expand="_group_expand_stage_id",
        index=True,
    )

    def _group_expand_stage_id(self, stages, domain, order):
        return stages.search([], order=order)

    def write(self, vals):
        if "stage_id" in vals:
            stage = self.env["estate.lead.match.stage"].browse(vals["stage_id"])
            raw_write = models.Model.write
            service = MatchTransitionFactory.create(self.env, raw_write)
            for match in self:
                service.transition(match, stage.code, fields.Datetime.now())
            return True
        return super().write(vals)

    def action_set_viewed(self):
        stage = self.env.ref("estate_kit.match_stage_viewed")
        self.write({"stage_id": stage.id})
        return self._reload_lead()

    def action_set_rejected(self):
        stage = self.env.ref("estate_kit.match_stage_rejected")
        self.write({"stage_id": stage.id})
        return self._reload_lead()

    def action_set_selected(self):
        stage = self.env.ref("estate_kit.match_stage_selected")
        self.write({"stage_id": stage.id})
        return self._reload_lead()

    def _reload_lead(self):
        return {
            "type": "ir.actions.act_window",
            "res_model": "crm.lead",
            "res_id": self.lead_id.id,
            "view_mode": "form",
            "target": "current",
        }

    def _cron_update_matching(self):
        leads = self.env["crm.lead"].search(
            [
                ("active", "=", True),
                ("probability", "not in", [100, 0]),
                ("search_property_type", "!=", False),
            ]
        )

        service = LeadMatcherFactory.create(self.env)

        for lead in leads:
            criteria = lead._build_match_criteria()
            service.match(lead.id, criteria)
