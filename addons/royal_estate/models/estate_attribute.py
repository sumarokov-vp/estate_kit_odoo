from odoo import fields, models


class EstateAttribute(models.Model):
    _name = "estate.attribute"
    _description = "Property Attribute"
    _order = "category, sequence, name"

    name = fields.Char(required=True, translate=True)
    code = fields.Char(required=True, index=True)
    field_type = fields.Selection(
        [
            ("char", "Text"),
            ("integer", "Integer"),
            ("float", "Float"),
            ("boolean", "Boolean"),
            ("selection", "Selection"),
            ("date", "Date"),
        ],
        required=True,
        default="char",
    )
    category = fields.Selection(
        [
            ("construction", "Construction"),
            ("area", "Area"),
            ("utilities", "Utilities"),
            ("amenities", "Amenities"),
            ("security", "Security"),
            ("features", "Features"),
            ("legal", "Legal"),
            ("commercial", "Commercial"),
            ("land", "Land"),
        ],
        required=True,
        default="features",
    )
    property_types = fields.Char(
        default="all",
        help="Comma-separated list: apartment,house,commercial,land or 'all'",
    )
    selection_options = fields.Text(
        help="JSON array of options: [{\"value\": \"code\", \"label\": \"Label\"}]"
    )
    sequence = fields.Integer(default=10)
    is_filterable = fields.Boolean(default=False)
    active = fields.Boolean(default=True)

    _sql_constraints = [
        ("code_unique", "UNIQUE(code)", "Attribute code must be unique"),
    ]
