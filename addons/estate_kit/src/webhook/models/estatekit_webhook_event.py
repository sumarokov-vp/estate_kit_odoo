from odoo import api, fields, models
from odoo.exceptions import ValidationError

from ..services.webhook_dispatcher import Factory as WebhookDispatcherFactory

WEBHOOK_EVENT_RETENTION_DAYS = 30


class EstateKitWebhookEvent(models.Model):
    _name = "estatekit.webhook.event"
    _description = "Processed Webhook Events"

    delivery_id = fields.Char(required=True, index=True)
    event_type = fields.Char()
    processed_at = fields.Datetime(default=fields.Datetime.now)

    @api.constrains("delivery_id")
    def _check_delivery_id_unique(self):
        for record in self:
            duplicate = self.search([
                ("delivery_id", "=", record.delivery_id),
                ("id", "!=", record.id),
            ], limit=1)
            if duplicate:
                raise ValidationError(f"Delivery already processed: {record.delivery_id}")

    def _cron_cleanup_old_events(self):
        WebhookDispatcherFactory.create(self.env).cleanup_old_events(WEBHOOK_EVENT_RETENTION_DAYS)

    @api.model
    def dispatch_event(self, event_type, payload):
        WebhookDispatcherFactory.create(self.env).dispatch(event_type, payload)
