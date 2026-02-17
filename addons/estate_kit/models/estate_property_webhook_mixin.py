import logging

from odoo import api, models

from ..services.api_client import EstateKitApiClient
from ..services.api_mapper import import_from_api_data
from ..services.api_mapper.importer import API_STATE_MAP

_logger = logging.getLogger(__name__)


class EstatePropertyWebhookMixin(models.AbstractModel):
    _name = "estate.property.webhook.mixin"
    _description = "Webhook handlers for estate properties"

    @api.model
    def _find_property_for_webhook(self, payload, event_name):
        property_id = payload.get("data", {}).get("property_id")
        if not property_id:
            _logger.warning("%s: missing property_id in payload", event_name)
            return None, None
        existing = self.search([("external_id", "=", property_id)], limit=1)
        if not existing:
            _logger.warning(
                "%s: property with external_id=%s not found", event_name, property_id
            )
        return property_id, existing

    @api.model
    def _handle_webhook_property_transition(self, payload):
        data = payload.get("data", {})
        status_id = data.get("status_id")
        property_id, existing = self._find_property_for_webhook(
            payload, "property.transition"
        )
        if not property_id:
            return

        new_state = API_STATE_MAP.get(status_id)
        if not new_state:
            _logger.warning(
                "property.transition: unknown status_id=%s for property %d",
                status_id,
                property_id,
            )
            return

        if not existing:
            return

        existing.with_context(
            skip_api_sync=True, force_state_change=True
        ).write({"state": new_state})
        _logger.info(
            "property.transition: property %d state → %s", property_id, new_state
        )

    @api.model
    def _handle_webhook_contact_request(self, payload):
        property_id, prop = self._find_property_for_webhook(
            payload, "contact_request.received"
        )
        if not property_id or not prop:
            return

        responsible_user = prop.user_id or prop.listing_agent_id
        if not responsible_user:
            _logger.warning(
                "contact_request.received: no responsible user for property id=%s",
                prop.id,
            )
            return

        data = payload.get("data", {})
        requester_tenant_id = data.get("requester_tenant_id")
        note = "Запрос контакта собственника"
        if requester_tenant_id:
            note += f" (tenant_id: {requester_tenant_id})"

        activity_type = self.env.ref("mail.mail_activity_data_todo")
        self.env["mail.activity"].create({
            "activity_type_id": activity_type.id,
            "summary": "Запрос контакта собственника",
            "note": note,
            "res_model_id": self.env["ir.model"]._get_id("estate.property"),
            "res_id": prop.id,
            "user_id": responsible_user.id,
        })

        _logger.info(
            "contact_request.received: created activity for property id=%s, user=%s",
            prop.id,
            responsible_user.login,
        )

    @api.model
    def _handle_webhook_mls_new_listing(self, payload):
        property_id = payload.get("data", {}).get("property_id")
        if not property_id:
            _logger.warning("mls.new_listing: missing property_id in payload")
            return

        existing = self.search([("external_id", "=", property_id)], limit=1)
        if existing:
            _logger.info("mls.new_listing: property with external_id=%d already exists", property_id)
            return

        client = EstateKitApiClient(self.env)
        item = client.get(f"/mls/properties/{property_id}")
        if not item:
            _logger.warning("mls.new_listing: failed to fetch property %d from API", property_id)
            return

        vals = import_from_api_data(self.env, item)
        vals["external_id"] = property_id
        vals["state"] = "mls_listed"
        self.with_context(skip_api_sync=True, force_state_change=True).create(vals)
        _logger.info("mls.new_listing: created property with external_id=%d", property_id)

    @api.model
    def _handle_webhook_mls_listing_removed(self, payload):
        property_id, existing = self._find_property_for_webhook(
            payload, "mls.listing_removed"
        )
        if not property_id or not existing:
            return
        existing.with_context(skip_api_sync=True, force_state_change=True).write({"state": "mls_removed"})
        _logger.info("mls.listing_removed: set mls_removed for property with external_id=%d", property_id)
