from odoo import fields, models


class EstateDistrict(models.Model):
    _name = "estate.district"
    _description = "District"
    _order = "name"

    name = fields.Char(required=True)
    code = fields.Char()
    active = fields.Boolean(default=True)
