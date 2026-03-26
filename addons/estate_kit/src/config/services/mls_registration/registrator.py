import logging
from typing import Any

from .action_helpers import notify, reload_settings
from .protocols import IApiClient

_logger = logging.getLogger(__name__)


class MlsRegistrator:
    def __init__(self, api_client: IApiClient, config_params: Any) -> None:
        self._api_client = api_client
        self._config_params = config_params

    def register(self, settings: Any) -> dict:
        if not self._api_client.api_url:
            return notify("Заполните URL API", "danger")

        company_name = settings.estate_kit_reg_company_name
        email = settings.estate_kit_reg_email
        phone = settings.estate_kit_reg_phone

        if not company_name or not email:
            return notify("Заполните название компании и email", "danger")

        payload: dict[str, str] = {"company_name": company_name, "email": email}
        if phone:
            payload["phone"] = phone
        base_url = (self._config_params.get_param("web.base.url") or "").replace("http://", "https://")
        if base_url:
            payload["webhook_url"] = f"{base_url}/estatekit/webhook"

        resp = self._api_client.post_public("/tenants/register", payload)
        if resp is None:
            return notify("Ошибка соединения с API", "danger")
        if resp.status_code not in (200, 201, 202):
            return notify(f"Ошибка API: {resp.status_code} {resp.text[:200]}", "danger")

        data = resp.json()
        _logger.info("MLS register response: status_code=%s, data=%s", resp.status_code, data)
        request_code = data.get("request_code", "")
        status = data.get("status", "pending")

        self._config_params.set_param("estate_kit.reg_request_code", request_code)
        self._config_params.set_param("estate_kit.reg_status", status)

        return reload_settings()
