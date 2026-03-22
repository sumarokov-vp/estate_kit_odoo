import json
import logging
from typing import Any

import requests

_logger = logging.getLogger(__name__)

ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"
ANTHROPIC_VERSION = "2023-06-01"
DEFAULT_MODEL = "claude-sonnet-4-5-20241022"
REQUEST_TIMEOUT = 60

SCORING_PROMPT = """\
Ты — эксперт по недвижимости в Казахстане. Оцени объект недвижимости по трём критериям \
по шкале от 1 до 10 (целое число).

**price_score** — конкурентность цены. 10 = значительно ниже рынка, 1 = сильно завышена.
**quality_score** — качество объекта и контента (состояние, ремонт, полнота описания, \
количество фото). 10 = отличное, 1 = очень плохое.
**marketing_score** — маркетинговый потенциал (насколько объект привлекателен для продвижения). \
10 = максимально привлекателен, 1 = непривлекателен.

Верни ТОЛЬКО валидный JSON без markdown-разметки:
{
  "price_score": <int 1-10>,
  "quality_score": <int 1-10>,
  "marketing_score": <int 1-10>,
  "rationale": "<краткое обоснование на русском, 2-3 предложения>"
}
"""


class AnthropicClient:
    def __init__(self, env: Any):
        config = env["ir.config_parameter"].sudo()
        self.api_key = config.get_param("estate_kit.anthropic_api_key") or ""
        self.model = config.get_param("estate_kit.anthropic_model") or DEFAULT_MODEL

    @property
    def is_configured(self) -> bool:
        return bool(self.api_key)

    def score_property(self, property_data: dict[str, Any]) -> dict[str, Any] | None:
        if not self.is_configured:
            _logger.warning("Anthropic API key is not configured")
            return None

        user_message = self._build_user_message(property_data)

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
                        {"role": "user", "content": user_message},
                    ],
                    "system": SCORING_PROMPT,
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

        return self._parse_response(response.json())

    def _build_user_message(self, data: dict[str, Any]) -> str:
        lines = ["Данные объекта недвижимости:"]
        field_labels = {
            "property_type": "Тип",
            "deal_type": "Тип сделки",
            "price": "Цена",
            "currency": "Валюта",
            "area_total": "Площадь (м²)",
            "rooms": "Комнат",
            "floor": "Этаж",
            "floors_total": "Этажность",
            "year_built": "Год постройки",
            "condition": "Состояние",
            "city": "Город",
            "district": "Район",
            "residential_complex": "ЖК",
            "description": "Описание",
            "photo_count": "Количество фото",
        }
        for key, label in field_labels.items():
            value = data.get(key)
            if value:
                lines.append(f"- {label}: {value}")
        return "\n".join(lines)

    def _parse_response(self, api_response: dict[str, Any]) -> dict[str, Any] | None:
        try:
            content = api_response["content"][0]["text"]
            # Strip possible markdown code fences
            text = content.strip()
            if text.startswith("```"):
                text = text.split("\n", 1)[1] if "\n" in text else text[3:]
                if text.endswith("```"):
                    text = text[:-3]
                text = text.strip()

            result = json.loads(text)

            # Validate scores
            for key in ("price_score", "quality_score", "marketing_score"):
                score = int(result[key])
                result[key] = max(1, min(10, score))

            result["rationale"] = str(result.get("rationale", ""))
            return result
        except (KeyError, IndexError, json.JSONDecodeError, ValueError, TypeError) as exc:
            _logger.error("Failed to parse Anthropic response: %s", exc)
            return None
