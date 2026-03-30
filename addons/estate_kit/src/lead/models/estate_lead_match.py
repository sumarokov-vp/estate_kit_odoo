from odoo import fields, models

from ..services.lead_matcher import Factory as LeadMatcherFactory


class EstateleadMatch(models.Model):
    _name = "estate.lead.match"
    _description = "Результат подбора"
    _order = "score desc, match_date desc"

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
    score = fields.Float(string="Совпадение")
    match_date = fields.Datetime(string="Дата подбора", default=fields.Datetime.now)
    state = fields.Selection(
        [
            ("new", "Новый"),
            ("viewed", "Просмотрен"),
            ("interested", "Интересен"),
            ("rejected", "Отклонён"),
        ],
        string="Статус",
        default="new",
    )

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
