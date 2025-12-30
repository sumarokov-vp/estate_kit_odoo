from odoo import fields, models


class CrmLead(models.Model):
    _inherit = "crm.lead"

    property_id = fields.Many2one(
        "estate.property",
        string="Property",
        help="Related property for this deal",
    )
    isa_user_id = fields.Many2one(
        "res.users",
        string="ISA",
        help="Inside Sales Agent who qualified the lead",
    )
    buyer_agent_id = fields.Many2one(
        "res.users",
        string="Buyer's Agent",
    )
    transaction_coordinator_id = fields.Many2one(
        "res.users",
        string="Transaction Coordinator",
    )
