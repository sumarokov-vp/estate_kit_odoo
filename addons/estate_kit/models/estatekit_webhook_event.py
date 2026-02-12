from odoo import fields, models


class EstateKitWebhookEvent(models.Model):
    _name = "estatekit.webhook.event"
    _description = "Processed Webhook Events"

    event_id = fields.Char(required=True, index=True)
    event_type = fields.Char()
    processed_at = fields.Datetime(default=fields.Datetime.now)

    _sql_constraints = [
        ("event_id_unique", "UNIQUE(event_id)", "Event already processed"),
    ]

    def _cron_cleanup_old_events(self):
        cutoff = fields.Datetime.subtract(fields.Datetime.now(), days=30)
        self.search([("processed_at", "<", cutoff)]).unlink()
