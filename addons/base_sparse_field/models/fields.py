from odoo import fields


class Serialized(fields.Json):
    """Serialized field - alias for Json field in Odoo 19.

    This field stores Python objects serialized as JSON in the database.
    In Odoo 19, the native Json field provides this functionality.
    """
    type = 'json'
