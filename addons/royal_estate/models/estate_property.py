from odoo import api, fields, models


class EstateProperty(models.Model):
    _name = "estate.property"
    _description = "Real Estate Property"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "create_date desc"

    name = fields.Char(string="Title", required=True, tracking=True)
    description = fields.Text()
    active = fields.Boolean(default=True)

    property_type = fields.Selection(
        [
            ("apartment", "Apartment"),
            ("house", "House"),
            ("commercial", "Commercial"),
            ("land", "Land"),
        ],
        required=True,
        default="apartment",
        tracking=True,
    )
    deal_type = fields.Selection(
        [
            ("sale", "Sale"),
            ("rent_long", "Long-term Rent"),
            ("rent_daily", "Daily Rent"),
        ],
        required=True,
        default="sale",
        tracking=True,
    )
    state = fields.Selection(
        [
            ("new", "New"),
            ("active", "Active"),
            ("deposit", "Deposit"),
            ("deal", "Deal"),
            ("canceled", "Canceled"),
            ("archived", "Archived"),
        ],
        required=True,
        copy=False,
        default="new",
        tracking=True,
    )

    price = fields.Monetary(tracking=True)
    currency_id = fields.Many2one(
        "res.currency",
        default=lambda self: self.env.company.currency_id,
    )
    rooms = fields.Integer()
    area_total = fields.Float(string="Total Area (m²)")

    district_id = fields.Many2one("estate.district", tracking=True)
    street = fields.Char()
    house_number = fields.Char()

    owner_id = fields.Many2one("res.partner", string="Owner", tracking=True)
    user_id = fields.Many2one(
        "res.users",
        string="Responsible",
        default=lambda self: self.env.user,
        tracking=True,
    )
    listing_coordinator_id = fields.Many2one(
        "res.users",
        string="Listing Coordinator",
        help="Who added the property to the database",
    )
    listing_agent_id = fields.Many2one(
        "res.users",
        string="Listing Agent",
    )

    source_id = fields.Many2one("estate.source", string="Source")
    contract_type = fields.Selection(
        [
            ("exclusive", "Exclusive"),
            ("non_exclusive", "Non-exclusive"),
        ],
    )
    contract_start = fields.Date()
    contract_end = fields.Date()
    is_shared = fields.Boolean(
        string="Shared Listing",
        help="Property is available for other agents",
    )

    internal_note = fields.Text(string="Internal Notes")
    video_url = fields.Char(string="Video URL")
    instagram_url = fields.Char(string="Instagram URL")

    attribute_value_ids = fields.One2many(
        "estate.property.attribute.value",
        "property_id",
        string="Attributes",
    )
    image_ids = fields.One2many(
        "estate.property.image",
        "property_id",
        string="Images",
    )

    def get_attribute_value(self, code):
        attr_value = self.attribute_value_ids.filtered(
            lambda v: v.attribute_id.code == code
        )
        if not attr_value:
            return None
        return attr_value._get_value()

    def set_attribute_value(self, code, value):
        attribute = self.env["estate.attribute"].search([("code", "=", code)], limit=1)
        if not attribute:
            return

        attr_value = self.attribute_value_ids.filtered(
            lambda v: v.attribute_id.code == code
        )

        field_name = f"value_{attribute.field_type}"
        vals = {"attribute_id": attribute.id, field_name: value}

        if attr_value:
            attr_value.write(vals)
        else:
            vals["property_id"] = self.id
            self.env["estate.property.attribute.value"].create(vals)

    @api.model
    def search_by_attribute(self, code, operator, value):
        attribute = self.env["estate.attribute"].search([("code", "=", code)], limit=1)
        if not attribute:
            return self.browse()

        field_name = f"value_{attribute.field_type}"
        attr_values = self.env["estate.property.attribute.value"].search(
            [
                ("attribute_id", "=", attribute.id),
                (field_name, operator, value),
            ]
        )
        return self.browse(attr_values.mapped("property_id.id"))
