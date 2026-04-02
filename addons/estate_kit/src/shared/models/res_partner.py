from odoo import fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    external_owner_id = fields.Integer(
        string="API Owner ID", index=True, copy=False
    )
    telegram_user_id = fields.Char(
        string="Telegram User ID", index=True, copy=False
    )
