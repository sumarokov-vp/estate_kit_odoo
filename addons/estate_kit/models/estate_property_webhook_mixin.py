import logging

from odoo import api, models

from ..services.api_client import EstateKitApiClient
from ..services.api_mapper import import_from_api_data

_logger = logging.getLogger(__name__)

STRING_STATE_MAP = {
    "active": "published",
    "rejected": "rejected",
    "suspended": "unpublished",
    "new": "moderation",
    "moderation": "moderation",
    "legal_review": "legal_review",
}


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
        status = data.get("status")
        property_id, existing = self._find_property_for_webhook(
            payload, "property.transition"
        )
        if not property_id:
            return

        new_state = STRING_STATE_MAP.get(status)
        if not new_state:
            _logger.warning(
                "property.transition: unknown status=%s for property %s",
                status,
                property_id,
            )
            return

        if not existing:
            return

        existing.with_context(
            skip_api_sync=True, force_state_change=True
        ).write({"state": new_state})
        _logger.info(
            "property.transition: property %s state → %s", property_id, new_state
        )

    @api.model
    def _handle_webhook_property_approved(self, payload):
        property_id, existing = self._find_property_for_webhook(
            payload, "property.approved"
        )
        if not property_id or not existing:
            return

        existing.with_context(
            skip_api_sync=True, force_state_change=True
        ).write({"state": "published"})
        _logger.info(
            "property.approved: property %s state → published", property_id
        )

    @api.model
    def _handle_webhook_property_rejected(self, payload):
        property_id, existing = self._find_property_for_webhook(
            payload, "property.rejected"
        )
        if not property_id or not existing:
            return

        data = payload.get("data", {})
        reason = data.get("reason", "")

        vals = {"state": "rejected"}
        if reason:
            vals["mls_rejection_reason"] = reason

        existing.with_context(
            skip_api_sync=True, force_state_change=True
        ).write(vals)

        responsible_user = existing.user_id or existing.listing_agent_id
        if responsible_user:
            activity_type = self.env.ref("mail.mail_activity_data_todo")
            note = f"Объект отклонён MLS: {reason}" if reason else "Объект отклонён MLS"
            self.env["mail.activity"].create({
                "activity_type_id": activity_type.id,
                "summary": "Объект отклонён MLS",
                "note": note,
                "res_model_id": self.env["ir.model"]._get_id("estate.property"),
                "res_id": existing.id,
                "user_id": responsible_user.id,
            })

        _logger.info(
            "property.rejected: property %s state → rejected, reason: %s",
            property_id, reason
        )

    @api.model
    def _handle_webhook_property_delisted(self, payload):
        property_id, existing = self._find_property_for_webhook(
            payload, "property.delisted"
        )
        if not property_id or not existing:
            return
        existing.with_context(
            skip_api_sync=True, force_state_change=True
        ).write({"state": "unpublished"})
        _logger.info(
            "property.delisted: property %s state → unpublished", property_id
        )

    @api.model
    def _handle_webhook_contact_request(self, payload):
        property_id, prop = self._find_property_for_webhook(
            payload, "contact.requested"
        )
        if not property_id or not prop:
            return

        responsible_user = prop.user_id or prop.listing_agent_id
        if not responsible_user:
            _logger.warning(
                "contact.requested: no responsible user for property id=%s",
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
            "contact.requested: created activity for property id=%s, user=%s",
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
