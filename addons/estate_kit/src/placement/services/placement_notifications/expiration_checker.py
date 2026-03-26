from odoo import fields


class ExpirationChecker:
    def expire(self, env) -> None:
        today = fields.Date.context_today(env["estate.property.placement"])
        expired = env["estate.property.placement"].search([
            ("state", "=", "active"),
            ("date_end", "!=", False),
            ("date_end", "<", today),
        ])
        expired.write({"state": "expired"})
