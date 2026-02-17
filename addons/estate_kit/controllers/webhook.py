import hashlib
import hmac
import json
import logging

from odoo import http
from odoo.http import request, Response

_logger = logging.getLogger(__name__)


class EstateKitWebhookController(http.Controller):

    @http.route("/estatekit/webhook", type="http", auth="none", methods=["POST"], csrf=False)
    def receive_webhook(self):
        body = request.httprequest.get_data()

        signature = request.httprequest.headers.get("X-EstateKit-Signature", "")
        event_type = request.httprequest.headers.get("X-EstateKit-Event", "")
        delivery_id = request.httprequest.headers.get("X-EstateKit-Delivery-Id", "")

        config = request.env["ir.config_parameter"].sudo()
        secret = config.get_param("estate_kit.webhook_secret") or ""

        if not secret:
            _logger.warning("Webhook received but webhook_secret is not configured")
            return Response("Webhook secret not configured", status=403)

        if not self._verify_signature(secret, body, signature):
            _logger.warning("Webhook signature verification failed for delivery %s", delivery_id)
            return Response("Invalid signature", status=401)

        try:
            payload = json.loads(body)
        except (json.JSONDecodeError, ValueError):
            _logger.warning("Webhook received invalid JSON for delivery %s", delivery_id)
            return Response("Invalid JSON", status=400)

        event_id = payload.get("event_id") or delivery_id
        if not event_id:
            return Response("Missing event_id", status=400)

        webhook_event = request.env["estatekit.webhook.event"].sudo()
        if webhook_event.search_count([("event_id", "=", event_id)], limit=1):
            _logger.info("Webhook event %s already processed, skipping", event_id)
            return Response("OK", status=200)

        webhook_event.create({"event_id": event_id, "event_type": event_type})

        self._dispatch_event(event_type, payload)

        return Response("OK", status=200)

    @staticmethod
    def _verify_signature(secret: str, body: bytes, signature: str) -> bool:
        if not signature:
            return False
        expected = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
        expected_full = f"sha256={expected}"
        return hmac.compare_digest(expected_full, signature)

    @staticmethod
    def _dispatch_event(event_type: str, payload: dict) -> None:
        _logger.info("Webhook event received: %s", event_type)

        property_model = request.env["estate.property"].sudo()

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
