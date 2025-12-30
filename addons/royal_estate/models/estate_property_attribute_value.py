from odoo import api, fields, models


class EstatePropertyAttributeValue(models.Model):
    _name = "estate.property.attribute.value"
    _description = "Property Attribute Value"

    property_id = fields.Many2one(
        "estate.property",
        required=True,
        ondelete="cascade",
        index=True,
    )
    attribute_id = fields.Many2one(
        "estate.attribute",
        required=True,
        ondelete="cascade",
        index=True,
    )
    attribute_code = fields.Char(related="attribute_id.code", store=True)
    field_type = fields.Selection(related="attribute_id.field_type", store=True)

    value_char = fields.Char()
    value_integer = fields.Integer()
    value_float = fields.Float()
    value_boolean = fields.Boolean()
    value_selection = fields.Char()
    value_date = fields.Date()

    _sql_constraints = [
        (
            "property_attribute_unique",
            "UNIQUE(property_id, attribute_id)",
            "Each attribute can only have one value per property",
        ),
    ]

    @api.depends("attribute_id", "value_char", "value_integer", "value_float", "value_boolean", "value_selection", "value_date")
    def _compute_display_name(self):
        for record in self:
            value = record._get_value()
            record.display_name = f"{record.attribute_id.name}: {value}"

    def _get_value(self):
        self.ensure_one()
        if self.field_type == "integer":
            return self.value_integer
        elif self.field_type == "float":
            return self.value_float
        elif self.field_type == "boolean":
            return self.value_boolean
        elif self.field_type == "selection":
            return self.value_selection
        elif self.field_type == "date":
            return self.value_date
        return self.value_char

    def _set_value(self, value):
        self.ensure_one()
        field_name = f"value_{self.field_type}"
        self.write({field_name: value})
