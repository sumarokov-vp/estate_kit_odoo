from datetime import date

from odoo import _, fields, models
from odoo.exceptions import UserError

from ..services.erp_core_client import Factory as ErpCoreClientFactory


class CommissionReportWizard(models.TransientModel):
    _name = "estate.commission.report.wizard"
    _description = "Отчёт по комиссиям ERP Core"

    employee_id = fields.Many2one(
        "res.users",
        string="Сотрудник",
    )
    date_from = fields.Date(
        string="Дата с",
        required=True,
        default=lambda self: date.today().replace(day=1),
    )
    date_to = fields.Date(
        string="Дата по",
        required=True,
        default=fields.Date.today,
    )
    partner_id = fields.Many2one(
        "res.partner",
        string="Контрагент",
    )

    line_ids = fields.One2many(
        "estate.commission.report.line",
        "wizard_id",
        string="Результаты",
        readonly=True,
    )

    employee_total = fields.Monetary(
        string="Итого комиссий сотрудника",
        currency_field="currency_id",
        readonly=True,
    )
    party_balance = fields.Monetary(
        string="Баланс контрагента",
        currency_field="currency_id",
        readonly=True,
    )
    currency_id = fields.Many2one(
        "res.currency",
        default=lambda self: self.env["res.currency"].search([("name", "=", "KZT")], limit=1),
        readonly=True,
    )

    def action_generate(self):
        self.ensure_one()

        if not self.employee_id and not self.partner_id:
            raise UserError(_("Укажите сотрудника или контрагента."))

        service = ErpCoreClientFactory.create()
        lines_data = []
        employee_total = 0
        party_balance = 0

        if self.employee_id:
            erp_employee_id = self._get_or_ensure_employee(service)
            if erp_employee_id:
                from datetime import datetime
                date_from_dt = datetime.combine(self.date_from, datetime.min.time())
                date_to_dt = datetime.combine(self.date_to, datetime.max.time())
                total = service.get_employee_commissions(
                    employee_party_id=erp_employee_id,
                    date_from=date_from_dt,
                    date_to=date_to_dt,
                )
                employee_total = float(total)
                lines_data.append({
                    "wizard_id": self.id,
                    "label": f"Комиссии сотрудника {self.employee_id.name} за период",
                    "amount": employee_total,
                    "line_type": "employee_commission",
                })

        if self.partner_id:
            erp_party_id = self._get_or_ensure_party(service)
            if erp_party_id:
                balance = service.get_party_balance(party_id=erp_party_id)
                party_balance = float(balance)
                lines_data.append({
                    "wizard_id": self.id,
                    "label": f"Баланс взаиморасчётов: {self.partner_id.name}",
                    "amount": party_balance,
                    "line_type": "party_balance",
                })

        self.line_ids.unlink()
        if lines_data:
            self.env["estate.commission.report.line"].create(lines_data)

        self.write({
            "employee_total": employee_total,
            "party_balance": party_balance,
        })

        return {
            "type": "ir.actions.act_window",
            "res_model": "estate.commission.report.wizard",
            "res_id": self.id,
            "view_mode": "form",
            "target": "new",
        }

    def _get_or_ensure_employee(self, service) -> int | None:
        user = self.employee_id
        employee = service.ensure_employee(
            odoo_user_id=user.id,
            name=user.name,
        )
        return employee

    def _get_or_ensure_party(self, service) -> int | None:
        partner = self.partner_id
        party = service.ensure_party(
            odoo_partner_id=partner.id,
            name=partner.name,
            party_type="company" if partner.is_company else "client",
        )
        return party
