import logging
from typing import Any

import requests

_logger = logging.getLogger(__name__)

ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"
ANTHROPIC_VERSION = "2023-06-01"
DEFAULT_MODEL = "claude-sonnet-4-5-20250514"
REQUEST_TIMEOUT = 60


class AnthropicClient:
    def __init__(self, env: Any):
        config = env["ir.config_parameter"].sudo()
        self.api_key = config.get_param("estate_kit.anthropic_api_key") or ""
        self.model = config.get_param("estate_kit.anthropic_model") or DEFAULT_MODEL

    @property
    def is_configured(self) -> bool:
        return bool(self.api_key)

    def complete(self, system: str, user: str) -> str | None:
        if not self.is_configured:
            _logger.warning("Anthropic API key is not configured")
            return None

        try:
            response = requests.post(
                ANTHROPIC_API_URL,
                headers={
                    "x-api-key": self.api_key,
                    "anthropic-version": ANTHROPIC_VERSION,
                    "content-type": "application/json",
                },
                json={
                    "model": self.model,
                    "max_tokens": 1024,
                    "messages": [
                        {"role": "user", "content": user},
                    ],
                    "system": system,
                },
                timeout=REQUEST_TIMEOUT,
            )
        except requests.RequestException as exc:
            _logger.error("Anthropic API request failed: %s", exc)
            return None

        if response.status_code != 200:
            _logger.error(
                "Anthropic API returned %d: %s",
                response.status_code,
                response.text[:500],
            )
            return None

        try:
            return response.json()["content"][0]["text"]
        except (KeyError, IndexError) as exc:
            _logger.error("Unexpected Anthropic API response format: %s", exc)
            return None
