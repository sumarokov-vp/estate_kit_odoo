from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    estate_kit_api_url = fields.Char(
        string="URL API",
        config_parameter="estate_kit.api_url",
    )
    estate_kit_api_key = fields.Char(
        string="API-ключ",
        config_parameter="estate_kit.api_key",
    )
    estate_kit_auto_mls = fields.Boolean(
        string="Авто-отправка в MLS",
        config_parameter="estate_kit.auto_mls",
        default=True,
    )
