from odoo import fields, models


class EstateClimateEquipment(models.Model):
    _name = "estate.climate.equipment"
    _description = "Климатическое оборудование"
    _order = "sequence, name"

    name = fields.Char(string="Название", required=True)
    code = fields.Char(string="Код", index=True)
    sequence = fields.Integer(string="Порядок", default=10)
    active = fields.Boolean(string="Активен", default=True)
