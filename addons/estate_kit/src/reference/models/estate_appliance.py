from odoo import fields, models


class EstateAppliance(models.Model):
    _name = "estate.appliance"
    _description = "Бытовая техника"
    _order = "sequence, name"

    name = fields.Char(string="Название", required=True)
    code = fields.Char(string="Код", index=True)
    sequence = fields.Integer(string="Порядок", default=10)
    active = fields.Boolean(string="Активен", default=True)
