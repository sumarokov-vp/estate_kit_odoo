import logging
import time
from typing import Any, BinaryIO

import requests

_logger = logging.getLogger(__name__)

REQUEST_TIMEOUT = 30
MAX_RETRIES = 3
RETRY_BASE_DELAY = 1
RETRYABLE_STATUS_CODES = range(500, 600)


class EstateKitApiClient:
    def __init__(self, env: Any):
        config = env["ir.config_parameter"].sudo()
        self.api_url = (config.get_param("estate_kit.api_url") or "").rstrip("/")
        self.api_key = config.get_param("estate_kit.api_key") or ""

    @property
    def _is_configured(self) -> bool:
        return bool(self.api_url and self.api_key)

    def _build_headers(self) -> dict[str, str]:
        return {
            "X-API-Key": self.api_key,
            "Accept": "application/json",
        }

    def _build_url(self, endpoint: str) -> str:
        endpoint = endpoint.lstrip("/")
        return f"{self.api_url}/{endpoint}"

    def _request_with_retry(
        self,
        method: str,
        url: str,
        **kwargs: Any,
    ) -> dict[str, Any] | None:
        if not self._is_configured:
            _logger.warning("EstateKit API is not configured (api_url or api_key missing)")
            return None

        kwargs.setdefault("timeout", REQUEST_TIMEOUT)
        kwargs.setdefault("headers", self._build_headers())

        last_exception: Exception | None = None

        for attempt in range(1, MAX_RETRIES + 1):
            try:
                _logger.info("API %s %s (attempt %d/%d)", method.upper(), url, attempt, MAX_RETRIES)
                response = requests.request(method, url, **kwargs)

                if response.status_code in RETRYABLE_STATUS_CODES:
                    _logger.warning(
                        "API %s %s returned %d (attempt %d/%d)",
                        method.upper(), url, response.status_code, attempt, MAX_RETRIES,
                    )
                    if attempt < MAX_RETRIES:
                        delay = RETRY_BASE_DELAY * (2 ** (attempt - 1))
                        time.sleep(delay)
                        continue
                    return None

                if response.status_code >= 400:
                    _logger.error(
                        "API %s %s returned %d: %s",
                        method.upper(), url, response.status_code, response.text[:500],
                    )
                    return None

                if response.status_code == 204 or not response.content:
                    return {}

                return response.json()

            except (requests.ConnectionError, requests.Timeout) as exc:
                last_exception = exc
                _logger.warning(
                    "API %s %s failed (attempt %d/%d): %s",
                    method.upper(), url, attempt, MAX_RETRIES, exc,
                )
                if attempt < MAX_RETRIES:
                    delay = RETRY_BASE_DELAY * (2 ** (attempt - 1))
                    time.sleep(delay)
                    continue

            except requests.RequestException as exc:
                _logger.error("API %s %s failed with non-retryable error: %s", method.upper(), url, exc)
                return None

        _logger.error(
            "API %s %s failed after %d attempts: %s",
            method.upper(), url, MAX_RETRIES, last_exception,
        )
        return None

    def get(self, endpoint: str, params: dict[str, Any] | None = None) -> dict[str, Any] | None:
        url = self._build_url(endpoint)
        return self._request_with_retry("GET", url, params=params)

    def post(self, endpoint: str, data: dict[str, Any]) -> dict[str, Any] | None:
        url = self._build_url(endpoint)
        headers = self._build_headers()
        headers["Content-Type"] = "application/json"
        return self._request_with_retry("POST", url, json=data, headers=headers)

    def put(self, endpoint: str, data: dict[str, Any]) -> dict[str, Any] | None:
        url = self._build_url(endpoint)
        headers = self._build_headers()
        headers["Content-Type"] = "application/json"
        return self._request_with_retry("PUT", url, json=data, headers=headers)

    def delete(self, endpoint: str) -> dict[str, Any] | None:
        url = self._build_url(endpoint)
        return self._request_with_retry("DELETE", url)

    def upload(
        self,
        endpoint: str,
        file_field: str,
        file_name: str,
        file_data: bytes | BinaryIO,
        extra_data: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        url = self._build_url(endpoint)
        files = {file_field: (file_name, file_data)}
        headers = {"X-API-Key": self.api_key, "Accept": "application/json"}
        return self._request_with_retry("POST", url, files=files, data=extra_data, headers=headers)
