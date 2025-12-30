from odoo import fields, models


class EstateDistrict(models.Model):
    _name = "estate.district"
    _description = "Район"
    _order = "name"

    name = fields.Char(string="Название", required=True)
    code = fields.Char(string="Код")
    active = fields.Boolean(string="Активен", default=True)
