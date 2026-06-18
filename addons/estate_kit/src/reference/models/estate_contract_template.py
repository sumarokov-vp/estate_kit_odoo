from odoo import fields, models


class EstateContractTemplate(models.Model):
    _name = "estate.contract.template"
    _description = "Тип договора"
    _order = "sequence, name"

    name = fields.Char(string="Название", required=True)
    code = fields.Char(string="Код", required=True)
    typst_file = fields.Char(
        string="Файл шаблона",
        help="Имя .typ-файла шаблона в каталоге report_templates/contracts/ модуля.",
    )
    sequence = fields.Integer(string="Порядок", default=10)
    active = fields.Boolean(string="Активен", default=True)

    _sql_constraints = [
        ("code_unique", "unique(code)", "Код типа договора должен быть уникальным."),
    ]
