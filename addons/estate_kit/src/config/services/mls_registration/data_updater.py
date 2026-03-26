import logging
from typing import Any

from .action_helpers import notify, reload_settings
from .protocols import IApiClient

_logger = logging.getLogger(__name__)


class DataUpdater:
    def __init__(self, api_client: IApiClient, config_params: Any) -> None:
        self._api_client = api_client
        self._config_params = config_params

    def update(self, settings: Any) -> dict:
        if not self._api_client.is_configured:
            return notify("API не настроен (нет URL или API-ключа)", "danger")

        payload: dict[str, str] = {}
        company_name = settings.estate_kit_reg_company_name
        phone = settings.estate_kit_reg_phone
        if company_name:
            payload["company_name"] = company_name
        if phone:
            payload["phone"] = phone
        base_url = (self._config_params.get_param("web.base.url") or "").replace("http://", "https://")
        if base_url:
            payload["webhook_url"] = f"{base_url}/estatekit/webhook"

        resp = self._api_client.post_raw("/tenants/update", payload)
        if resp is None:
            return notify("Ошибка соединения с API", "danger")
        if resp.status_code == 404:
            return notify("Активная подписка не найдена", "warning")
        if resp.status_code == 422:
            return notify("Нет полей для обновления", "warning")
        if resp.status_code == 200:
            return notify("Данные совпадают, изменений нет", "info")
        if resp.status_code == 202:
            data = resp.json()
            request_code = data.get("request_code", "")
            self._config_params.set_param("estate_kit.reg_request_code", request_code)
            self._config_params.set_param("estate_kit.reg_status", "pending_update")
            return reload_settings()

        return notify(f"Ошибка API: {resp.status_code} {resp.text[:200]}", "danger")
