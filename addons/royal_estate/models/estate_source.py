from odoo import fields, models


class EstateSource(models.Model):
    _name = "estate.source"
    _description = "Customer Source"
    _order = "sequence, name"

    name = fields.Char(required=True)
    code = fields.Char()
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)
