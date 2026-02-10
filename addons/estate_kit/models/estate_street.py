from odoo import fields, models


class EstateStreet(models.Model):
    _name = "estate.street"
    _description = "Улица"
    _order = "name"

    name = fields.Char(string="Название", required=True, index=True)
    city_id = fields.Many2one(
        "estate.city",
        string="Город",
        required=True,
        ondelete="restrict",
        index=True,
    )
    district_id = fields.Many2one(
        "estate.district",
        string="Район",
        ondelete="restrict",
    )
    active = fields.Boolean(string="Активен", default=True)
