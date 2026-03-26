from odoo import fields, models


class EstateCity(models.Model):
    _name = "estate.city"
    _description = "Город"
    _order = "sequence, name"

    name = fields.Char(string="Название", required=True)
    code = fields.Char(string="Код", index=True)
    sequence = fields.Integer(string="Порядок", default=10)
    active = fields.Boolean(string="Активен", default=True)

    district_ids = fields.One2many(
        "estate.district",
        "city_id",
        string="Районы",
    )
