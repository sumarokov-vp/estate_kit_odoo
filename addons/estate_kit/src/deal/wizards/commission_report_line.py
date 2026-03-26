from odoo import fields, models


class CommissionReportLine(models.TransientModel):
    _name = "estate.commission.report.line"
    _description = "Строка отчёта по комиссиям"

    wizard_id = fields.Many2one(
        "estate.commission.report.wizard",
        ondelete="cascade",
    )
    label = fields.Char(string="Описание", readonly=True)
    amount = fields.Float(string="Сумма", digits=(16, 2), readonly=True)
    line_type = fields.Selection(
        [
            ("employee_commission", "Комиссия сотрудника"),
            ("party_balance", "Баланс контрагента"),
        ],
        string="Тип",
        readonly=True,
    )
