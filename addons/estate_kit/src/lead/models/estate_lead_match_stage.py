from odoo import fields, models


class EstateLeadMatchStage(models.Model):
    _name = "estate.lead.match.stage"
    _description = "Стадия подбора"
    _order = "sequence"

    name = fields.Char(string="Название", required=True, translate=True)
    sequence = fields.Integer(string="Порядок", default=10)
    code = fields.Char(string="Код", required=True)
    fold = fields.Boolean(string="Свёрнута")
