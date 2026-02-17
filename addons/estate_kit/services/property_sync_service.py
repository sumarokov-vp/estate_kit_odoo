import logging
from typing import Any

from odoo.exceptions import UserError

from .api_client import EstateKitApiClient
from .api_mapper import prepare_api_payload

_logger = logging.getLogger(__name__)


class PropertySyncService:
    def __init__(self, env: Any):
        self.env = env
        self.client = EstateKitApiClient(env)

    def push_owner(self, record) -> int | None:
        if not record.owner_id:
            return None
        if not self.client.is_configured:
            return None
        partner = record.owner_id
        if partner.external_owner_id:
            return partner.external_owner_id
        payload = {"name": partner.name, "phone": partner.phone or ""}
        response = self.client.post("/owners", payload)
        if response and "id" in response:
            partner.write({"external_owner_id": response["id"]})
            return response["id"]
        return None

    def push_property(self, record) -> None:
        if not self.client.is_configured:
            raise UserError(
                "API не настроен. Укажите API URL и API Key в "
                "Настройки → Технические → Параметры системы "
                "(estate_kit.api_url и estate_kit.api_key)."
            )
        payload = prepare_api_payload(record)
        response = self.client.post("/properties", payload)
        if response and response.get("id"):
            record.with_context(skip_api_sync=True).write(
                {"external_id": response["id"]}
            )
            owner_data = response.get("owner")
            if (
                owner_data
                and owner_data.get("created")
                and owner_data.get("id")
                and record.owner_id
            ):
                record.owner_id.write({"external_owner_id": owner_data["id"]})
