from odoo import api, fields, models

from ..services.deal_state_machine import Factory as DealStateMachineFactory


class EstateDeal(models.Model):
    _name = "estate.deal"
    _description = "Сделка"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "create_date desc"

    name = fields.Char(
        string="Номер сделки",
        readonly=True,
        default="Новая сделка",
    )
    lead_id = fields.Many2one(
        "crm.lead",
        string="Лид",
        ondelete="set null",
    )
    property_id = fields.Many2one(
        "estate.property",
        string="Объект",
        ondelete="set null",
    )
    deal_type = fields.Selection(
        [
            ("sale", "Продажа"),
            ("rent", "Аренда"),
        ],
        string="Тип сделки",
        required=True,
        default="sale",
        tracking=True,
    )
    state = fields.Selection(
        [
            ("draft", "Черновик"),
            ("confirmed", "Подтверждена"),
            ("in_progress", "В работе"),
            ("closing", "Закрытие"),
            ("done", "Завершена"),
            ("cancelled", "Отменена"),
        ],
        string="Статус",
        default="draft",
        required=True,
        tracking=True,
    )
    currency_id = fields.Many2one(
        "res.currency",
        string="Валюта",
        default=lambda self: self.env.company.currency_id,
        required=True,
    )
    deal_price = fields.Monetary(
        string="Сумма сделки",
        currency_field="currency_id",
        tracking=True,
    )
    client_partner_id = fields.Many2one(
        "res.partner",
        string="Покупатель",
        ondelete="set null",
    )
    owner_partner_id = fields.Many2one(
        "res.partner",
        string="Собственник",
        ondelete="set null",
    )
    date_deal = fields.Date(string="Дата сделки")
    date_closing = fields.Date(string="Дата закрытия")
    commission_percent = fields.Float(
        string="Комиссия, %",
        digits=(5, 2),
        default=0.0,
    )
    total_commission = fields.Monetary(
        string="Сумма комиссии",
        currency_field="currency_id",
        compute="_compute_total_commission",
        store=True,
    )
    participant_ids = fields.One2many(
        "estate.deal.participant",
        "deal_id",
        string="Участники",
    )
    erp_invoice_id = fields.Char(
        string="UUID Invoice (ERP Core)",
        readonly=True,
    )
    note = fields.Html(string="Примечания")

    @api.depends("deal_price", "commission_percent")
    def _compute_total_commission(self):
        for record in self:
            record.total_commission = record.deal_price * record.commission_percent / 100

    def action_confirm(self):
        DealStateMachineFactory.create(self.env).confirm(self)

    def action_start(self):
        DealStateMachineFactory.create(self.env).start(self)

    def action_closing(self):
        DealStateMachineFactory.create(self.env).closing(self)

    def action_complete(self):
        DealStateMachineFactory.create(self.env).complete(self)

    def action_cancel(self):
        DealStateMachineFactory.create(self.env).cancel(self)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("name", "Новая сделка") == "Новая сделка":
                vals["name"] = self.env["ir.sequence"].next_by_code("estate.deal") or "Новая сделка"
        return super().create(vals_list)
