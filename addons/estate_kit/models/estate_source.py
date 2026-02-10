from odoo import fields, models


class EstateSource(models.Model):
    _name = "estate.source"
    _description = "Источник клиента"
    _order = "sequence, name"

    name = fields.Char(string="Название", required=True)
    code = fields.Char(string="Код")
    sequence = fields.Integer(string="Порядок", default=10)
    active = fields.Boolean(string="Активен", default=True)
