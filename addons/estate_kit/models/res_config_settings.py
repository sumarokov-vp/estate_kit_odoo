import logging

from odoo import fields, models

from ..services.api_client import EstateKitApiClient

_logger = logging.getLogger(__name__)

WEBHOOK_EVENTS = [
    "property.transition.*",
    "property.locked",
    "property.unlocked",
    "mls.new_listing",
    "mls.listing_updated",
    "mls.listing_removed",
    "contact_request.received",
]


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    estate_kit_api_url = fields.Char(
        string="URL API",
        config_parameter="estate_kit.api_url",
    )
    estate_kit_api_key = fields.Char(
        string="API-ключ",
        config_parameter="estate_kit.api_key",
    )
    estate_kit_webhook_secret = fields.Char(
        string="Webhook Secret",
        config_parameter="estate_kit.webhook_secret",
    )
    estate_kit_webhook_url = fields.Char(
        string="Webhook URL",
        config_parameter="estate_kit.webhook_url",
    )

    def set_values(self):
        config = self.env["ir.config_parameter"].sudo()
        old_url = config.get_param("estate_kit.webhook_url") or ""
        old_secret = config.get_param("estate_kit.webhook_secret") or ""

        super().set_values()

        new_url = self.estate_kit_webhook_url or ""
        new_secret = self.estate_kit_webhook_secret or ""

        if new_url == old_url and new_secret == old_secret:
            return

        self._register_webhook(config, new_url, new_secret, old_url)

    def _register_webhook(self, config, new_url, new_secret, old_url):
        client = EstateKitApiClient(self.env)
        if not client._is_configured:
            _logger.warning("Cannot register webhook: API not configured")
            return

        old_subscription_id = config.get_param("estate_kit.webhook_subscription_id") or ""

        if old_subscription_id and old_url != new_url:
            result = client.delete(f"/webhooks/{old_subscription_id}")
            if result is not None:
                _logger.info("Deleted old webhook subscription %s", old_subscription_id)
            config.set_param("estate_kit.webhook_subscription_id", "")

        if not new_url or not new_secret:
            return

        result = client.post("/webhooks", {
            "url": new_url,
            "secret": new_secret,
            "events": WEBHOOK_EVENTS,
        })

        if result and result.get("id"):
            config.set_param("estate_kit.webhook_subscription_id", result["id"])
            _logger.info("Registered webhook subscription %s", result["id"])
        else:
            _logger.warning("Failed to register webhook subscription")
