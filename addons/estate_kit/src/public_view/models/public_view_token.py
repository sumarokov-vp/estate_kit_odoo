import uuid
from datetime import timedelta

from odoo import api, fields, models

from ..services.url_builder import Factory as UrlBuilderFactory

_DEFAULT_TTL_DAYS = 30


class EstatePropertyPublicViewToken(models.Model):
    _name = "estate.property.public.view.token"
    _description = "Property Public View Token"
    _order = "create_date desc"

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
    def get_or_create_url(self, property_id, ttl_days=_DEFAULT_TTL_DAYS):
        record = self._find_active(property_id)
        if not record:
            record = self._create_token(property_id, ttl_days)
        return UrlBuilderFactory.create(self.env).public_view_url(record.token)

    @api.model
    def regenerate_url(self, property_id, ttl_days=_DEFAULT_TTL_DAYS):
        self.search([("property_id", "=", property_id)]).write({"is_active": False})
        record = self._create_token(property_id, ttl_days)
        return UrlBuilderFactory.create(self.env).public_view_url(record.token)

    def _validate_token(self, token):
        return self.search(
            [
                ("token", "=", token),
                ("is_active", "=", True),
                ("expires_at", ">", fields.Datetime.now()),
            ],
            limit=1,
        )

    def _find_active(self, property_id):
        return self.search(
            [
                ("property_id", "=", property_id),
                ("is_active", "=", True),
                ("expires_at", ">", fields.Datetime.now()),
            ],
            limit=1,
            order="expires_at desc",
        )

    def _create_token(self, property_id, ttl_days):
        return self.create(
            {
                "property_id": property_id,
                "token": uuid.uuid4().hex,
                "expires_at": fields.Datetime.now() + timedelta(days=ttl_days),
            }
        )
