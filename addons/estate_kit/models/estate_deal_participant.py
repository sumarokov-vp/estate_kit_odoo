from odoo import api, fields, models


class EstateDealParticipant(models.Model):
    _name = "estate.deal.participant"
    _description = "Участник сделки"

    deal_id = fields.Many2one(
        "estate.deal",
        string="Сделка",
        required=True,
        ondelete="cascade",
    )
    role = fields.Selection(
        [
            ("listing_agent", "Листинговый агент"),
            ("buyer_agent", "Агент покупателя"),
            ("team_lead", "Тим-лид"),
            ("isa", "ISA"),
            ("coordinator", "Координатор"),
            ("legal", "Юрист"),
            ("referral", "Реферал"),
            ("mls_fee", "Комиссия MLS"),
        ],
        string="Роль",
        required=True,
    )
    user_id = fields.Many2one(
        "res.users",
        string="Сотрудник",
        ondelete="set null",
    )
    partner_id = fields.Many2one(
        "res.partner",
        string="Внешний участник",
        ondelete="set null",
    )
    tenant_id = fields.Char(string="Тенант MLS")
    commission_percent = fields.Float(
        string="Комиссия, %",
        digits=(5, 2),
        default=0.0,
    )
    currency_id = fields.Many2one(
        related="deal_id.currency_id",
        store=True,
    )
    commission_amount = fields.Monetary(
        string="Сумма комиссии",
        currency_field="currency_id",
        compute="_compute_commission_amount",
        store=True,
    )
    erp_employee_id = fields.Char(string="UUID Employee (ERP Core)")

    @api.depends("deal_id.total_commission", "commission_percent")
    def _compute_commission_amount(self):
        for record in self:
            record.commission_amount = record.deal_id.total_commission * record.commission_percent / 100
