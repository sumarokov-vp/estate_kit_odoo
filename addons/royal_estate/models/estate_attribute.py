from odoo import fields, models


class EstateAttribute(models.Model):
    _name = "estate.attribute"
    _description = "Атрибут объекта"
    _order = "category, sequence, name"

    name = fields.Char(string="Название", required=True, translate=True)
    code = fields.Char(string="Код", required=True, index=True)

    _constraints = [
        models.Constraint(
            "UNIQUE(code)",
            "Код атрибута должен быть уникальным",
        ),
    ]
    field_type = fields.Selection(
        [
            ("char", "Текст"),
            ("integer", "Целое число"),
            ("float", "Дробное число"),
            ("boolean", "Да/Нет"),
            ("selection", "Выбор из списка"),
            ("date", "Дата"),
        ],
        string="Тип данных",
        required=True,
        default="char",
    )
    category = fields.Selection(
        [
            ("construction", "Строение"),
            ("area", "Площади"),
            ("utilities", "Коммуникации"),
            ("amenities", "Удобства"),
            ("security", "Безопасность"),
            ("features", "Особенности"),
            ("legal", "Юридическое"),
            ("commercial", "Коммерция"),
            ("land", "Земля"),
        ],
        string="Категория",
        required=True,
        default="features",
    )
    property_types = fields.Char(
        string="Типы объектов",
        default="all",
        help="Через запятую: apartment,house,commercial,land или 'all'",
    )
    selection_options = fields.Text(
        string="Варианты выбора",
        help="JSON массив: [{\"value\": \"код\", \"label\": \"Название\"}]"
    )
    sequence = fields.Integer(string="Порядок", default=10)
    is_filterable = fields.Boolean(string="Доступен в фильтрах", default=False)
    active = fields.Boolean(string="Активен", default=True)
