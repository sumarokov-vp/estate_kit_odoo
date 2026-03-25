from odoo import fields, models


class CrmLeadMatching(models.Model):
    _inherit = "crm.lead"

    last_matching_date = fields.Datetime(
        string="Last Matching Date",
        readonly=True,
        copy=False,
    )
    match_ids = fields.One2many(
        "estate.lead.match",
        "lead_id",
        string="Matched Properties",
    )
    match_count = fields.Integer(
        string="Matches",
        compute="_compute_match_count",
    )

    def _compute_match_count(self):
        for rec in self:
            rec.match_count = len(rec.match_ids)
