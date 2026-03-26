from odoo import fields, models


class EstatePropertyTag(models.Model):
    _name = "estate.property.tag"
    _description = "Тег объекта недвижимости"
    _order = "name"

    name = fields.Char(string="Название", required=True)
    color = fields.Integer(string="Цвет")
