import uuid
from datetime import timedelta

from odoo import api, fields, models


class EstatePropertyUploadToken(models.Model):
    _name = "estate.property.upload.token"
    _description = "Property Photo Upload Token"

    property_id = fields.Many2one(
        "estate.property",
        required=True,
        ondelete="cascade",
        index=True,
    )
    token = fields.Char(required=True, index=True, copy=False)
    expires_at = fields.Datetime(required=True)
    is_active = fields.Boolean(default=True)

    @api.model
    def generate_token(self, property_id, ttl_days=7):
        token = uuid.uuid4().hex
        self.create(
            {
                "property_id": property_id,
                "token": token,
                "expires_at": fields.Datetime.now() + timedelta(days=ttl_days),
            }
        )
        base_url = (
            self.env["ir.config_parameter"].sudo().get_param("web.base.url") or ""
        )
        return f"{base_url}/estate_kit/upload/{token}"

    def _validate_token(self, token):
        return self.search(
            [
                ("token", "=", token),
                ("is_active", "=", True),
                ("expires_at", ">", fields.Datetime.now()),
            ],
            limit=1,
        )
