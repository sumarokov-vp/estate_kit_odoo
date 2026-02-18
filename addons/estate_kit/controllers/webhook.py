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
        event_type = request.httprequest.headers.get("X-Event-Type", "")
        delivery_id = request.httprequest.headers.get("X-Delivery-Id", "")

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

        delivery_id = payload.get("delivery_id") or delivery_id
        if not delivery_id:
            return Response("Missing delivery_id", status=400)

        webhook_event = request.env["estatekit.webhook.event"].sudo()
        if webhook_event.search_count([("delivery_id", "=", delivery_id)], limit=1):
            _logger.info("Webhook delivery %s already processed, skipping", delivery_id)
            return Response("OK", status=200)

        webhook_event.create({"delivery_id": delivery_id, "event_type": event_type})

        webhook_event.dispatch_event(event_type, payload)

        return Response("OK", status=200)

    @staticmethod
    def _verify_signature(secret: str, body: bytes, signature: str) -> bool:
        if not signature:
            return False
        expected = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
        expected_full = f"sha256={expected}"
        return hmac.compare_digest(expected_full, signature)
