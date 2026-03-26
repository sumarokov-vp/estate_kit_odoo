import logging
from typing import Any

from .action_helpers import notify, reload_settings
from .protocols import IApiClient

_logger = logging.getLogger(__name__)


class StatusChecker:
    def __init__(self, api_client: IApiClient, config_params: Any) -> None:
        self._api_client = api_client
        self._config_params = config_params

    def check(self, settings: Any) -> dict:
        request_code = self._config_params.get_param("estate_kit.reg_request_code") or ""
        email = self._config_params.get_param("estate_kit.reg_email") or ""
        current_status = self._config_params.get_param("estate_kit.reg_status") or ""

        if not request_code:
            return notify("Нет данных для проверки", "danger")

        if current_status == "pending_update":
            if not self._api_client.is_configured:
                return notify("API не настроен (нет URL или API-ключа)", "danger")
            endpoint = f"/tenants/update/{request_code}"
            resp = self._api_client.get_raw(endpoint)
        else:
            if not self._api_client.api_url or not email:
                return notify("Нет данных для проверки", "danger")
            endpoint = f"/tenants/register/{request_code}"
            resp = self._api_client.get_public(endpoint, params={"email": email})

        if resp is None:
            return notify("Ошибка соединения с API", "danger")
        if resp.status_code == 404:
            self._config_params.set_param("estate_kit.reg_request_code", "")
            self._config_params.set_param("estate_kit.reg_status", "")
            return reload_settings()
        if resp.status_code != 200:
            return notify(f"Ошибка API: {resp.status_code}", "danger")

        data = resp.json()
        status = data.get("status", "unknown")

        if status == "approved":
            if current_status != "pending_update":
                if data.get("api_key"):
                    self._config_params.set_param("estate_kit.api_key", data["api_key"])
                if data.get("webhook_secret"):
                    self._config_params.set_param("estate_kit.webhook_secret", data["webhook_secret"])
            self._config_params.set_param("estate_kit.reg_request_code", "")
            self._config_params.set_param("estate_kit.reg_status", "")
        else:
            self._config_params.set_param("estate_kit.reg_status", status)

        return reload_settings()
