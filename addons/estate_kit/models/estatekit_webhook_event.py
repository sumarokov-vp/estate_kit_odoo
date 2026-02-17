import logging

from odoo import api, fields, models
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)

WEBHOOK_EVENT_RETENTION_DAYS = 30


class EstateKitWebhookEvent(models.Model):
    _name = "estatekit.webhook.event"
    _description = "Processed Webhook Events"

    event_id = fields.Char(required=True, index=True)
    event_type = fields.Char()
    processed_at = fields.Datetime(default=fields.Datetime.now)

    @api.constrains("event_id")
    def _check_event_id_unique(self):
        for record in self:
            duplicate = self.search([
                ("event_id", "=", record.event_id),
                ("id", "!=", record.id),
            ], limit=1)
            if duplicate:
                raise ValidationError(f"Event already processed: {record.event_id}")

    def _cron_cleanup_old_events(self):
        cutoff = fields.Datetime.subtract(fields.Datetime.now(), days=WEBHOOK_EVENT_RETENTION_DAYS)
        self.search([("processed_at", "<", cutoff)]).unlink()

    @api.model
    def dispatch_event(self, event_type, payload):
        _logger.info("Webhook event received: %s", event_type)

        property_model = self.env["estate.property"].sudo()

        if event_type in (
            "property.created",
            "property.approved",
            "property.suspended",
            "property.resumed",
        ):
            property_model._handle_webhook_property_transition(payload)
        elif event_type == "contact_request.received":
            property_model._handle_webhook_contact_request(payload)
        elif event_type == "mls.new_listing":
            property_model._handle_webhook_mls_new_listing(payload)
        elif event_type == "mls.listing_removed":
            property_model._handle_webhook_mls_listing_removed(payload)
