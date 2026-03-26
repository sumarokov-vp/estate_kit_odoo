from odoo import api, models

from ..services.webhook_handlers import Factory as WebhookHandlersFactory


class EstatePropertyWebhookMixin(models.AbstractModel):
    _name = "estate.property.webhook.mixin"
    _description = "Webhook handlers for estate properties"

    @api.model
    def _handle_webhook_property_transition(self, payload):
        WebhookHandlersFactory.create(self.env).handle_transition(payload)

    @api.model
    def _handle_webhook_property_approved(self, payload):
        WebhookHandlersFactory.create(self.env).handle_approved(payload)

    @api.model
    def _handle_webhook_property_rejected(self, payload):
        WebhookHandlersFactory.create(self.env).handle_rejected(payload)

    @api.model
    def _handle_webhook_property_delisted(self, payload):
        WebhookHandlersFactory.create(self.env).handle_delisted(payload)

    @api.model
    def _handle_webhook_contact_request(self, payload):
        WebhookHandlersFactory.create(self.env).handle_contact_request(payload)

    @api.model
    def _handle_webhook_mls_new_listing(self, payload):
        WebhookHandlersFactory.create(self.env).handle_new_listing(payload)

    @api.model
    def _handle_webhook_mls_listing_removed(self, payload):
        WebhookHandlersFactory.create(self.env).handle_listing_removed(payload)
