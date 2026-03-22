import json
import logging
from typing import Any

import requests

_logger = logging.getLogger(__name__)

ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"
ANTHROPIC_VERSION = "2023-06-01"
DEFAULT_MODEL = "claude-sonnet-4-5-20250514"
REQUEST_TIMEOUT = 60

# ---------------------------------------------------------------------------
# Системные промпты по типу недвижимости
# ---------------------------------------------------------------------------

_SCORING_BASE = """\
Ты — эксперт по недвижимости в Казахстане. Оцени объект по трём критериям \
по шкале от 1 до 10 (целое число).

**price_score** — конкурентность цены относительно рынка. \
10 = значительно ниже рынка, 1 = сильно завышена. \
"Цена" — стоимость ВСЕГО объекта целиком, НЕ за квадратный метр. \
Также указана рассчитанная цена за м² — используй оба значения.

**quality_score** — качество объекта на фоне рынка. \
{quality_criteria}

**listing_score** — качество карточки объекта в базе. \
{listing_criteria}

{optional_note}

Верни ТОЛЬКО валидный JSON без markdown-разметки:
{{"price_score": <int 1-10>, "quality_score": <int 1-10>, \
"listing_score": <int 1-10>, \
"rationale": "<краткое обоснование на русском, по каждому критерию 1 предложение>"}}
"""

_OPTIONAL_NOTE = """\
ВАЖНО: Некоторые поля являются опциональными и помечены как «(опц.)». \
Отсутствие опционального поля — НЕ является недостатком карточки. \
Например, поле «ЖК» заполняется только если объект находится в жилом комплексе; \
его отсутствие не снижает listing_score."""

SCORING_PROMPTS: dict[str, str] = {
    "apartment": _SCORING_BASE.format(
        quality_criteria=(
            "Оцени привлекательность квартиры для покупателя/арендатора: "
            "состояние/ремонт, расположение (город, район), планировка "
            "(площадь общая/жилая/кухня, комнаты, этаж/этажность), "
            "год постройки, тип строения, удобства (санузел, балкон, мебель, паркинг). "
            "10 = отличная квартира, 1 = слабый объект."
        ),
        listing_criteria=(
            "Полнота карточки квартиры: фотографии (хорошо: 10+, мало: <5), "
            "описание, заполненность ключевых характеристик "
            "(площадь, комнаты, этаж, состояние, район, тип строения). "
            "10 = идеально заполнена, 1 = данных критически мало."
        ),
        optional_note=_OPTIONAL_NOTE,
    ),
    "house": _SCORING_BASE.format(
        quality_criteria=(
            "Оцени привлекательность дома: площадь дома и участка, "
            "материал стен, фундамент, крыша, состояние/ремонт, "
            "год постройки, коммуникации (вода, канализация, газ, электричество), "
            "расположение (город, район). "
            "10 = отличный дом, 1 = слабый объект."
        ),
        listing_criteria=(
            "Полнота карточки дома: фотографии (хорошо: 10+, мало: <5), "
            "описание, заполненность ключевых характеристик "
            "(площадь дома, площадь участка, материал стен, коммуникации, состояние). "
            "10 = идеально заполнена, 1 = данных критически мало."
        ),
        optional_note=_OPTIONAL_NOTE,
    ),
    "townhouse": _SCORING_BASE.format(
        quality_criteria=(
            "Оцени привлекательность таунхауса: площадь, этажность, "
            "состояние/ремонт, год постройки, площадь участка, "
            "коммуникации, расположение (город, район). "
            "10 = отличный таунхаус, 1 = слабый объект."
        ),
        listing_criteria=(
            "Полнота карточки таунхауса: фотографии (хорошо: 10+, мало: <5), "
            "описание, заполненность ключевых характеристик "
            "(площадь, этажность, участок, коммуникации, состояние). "
            "10 = идеально заполнена, 1 = данных критически мало."
        ),
        optional_note=_OPTIONAL_NOTE,
    ),
    "commercial": _SCORING_BASE.format(
        quality_criteria=(
            "Оцени привлекательность коммерческого помещения: "
            "назначение (офис/торговля/склад/производство), площадь общая/торговая/складская, "
            "этаж, высота потолков, отдельный вход, витрины, паркинг, "
            "расположение (город, район). "
            "10 = отличный объект, 1 = слабый."
        ),
        listing_criteria=(
            "Полнота карточки коммерции: фотографии (хорошо: 10+, мало: <5), "
            "описание, заполненность характеристик "
            "(площадь, назначение, этаж, состояние). "
            "10 = идеально заполнена, 1 = данных критически мало."
        ),
        optional_note=_OPTIONAL_NOTE,
    ),
    "land": _SCORING_BASE.format(
        quality_criteria=(
            "Оцени привлекательность земельного участка: "
            "площадь (сотки), категория земли (ИЖС/СНТ/ЛПХ/коммерция), "
            "наличие коммуникаций (вода, канализация, газ, электричество), "
            "подъездная дорога, расположение (город, район). "
            "10 = отличный участок, 1 = слабый."
        ),
        listing_criteria=(
            "Полнота карточки участка: фотографии (хорошо: 5+, мало: <3), "
            "описание, заполненность характеристик "
            "(площадь, категория земли, коммуникации, подъездная дорога). "
            "10 = идеально заполнена, 1 = данных критически мало."
        ),
        optional_note=_OPTIONAL_NOTE,
    ),
}

# ---------------------------------------------------------------------------
# Наборы атрибутов по типу недвижимости
# ---------------------------------------------------------------------------

# (field_name, label, optional) — optional=True значит необязательное поле
_COMMON_FIELDS: list[tuple[str, str, bool]] = [
    ("property_type", "Тип", False),
    ("deal_type", "Тип сделки", False),
    ("price", "Цена (за весь объект)", False),
    ("price_per_sqm", "Цена за м²", False),
    ("currency", "Валюта", False),
    ("area_total", "Общая площадь (м²)", False),
    ("city", "Город", False),
    ("district", "Район", False),
    ("year_built", "Год постройки", True),
    ("description", "Описание", True),
    ("photo_count", "Количество фото", False),
    ("parking", "Парковка", True),
    ("heating", "Отопление", True),
]

PROPERTY_TYPE_FIELDS: dict[str, list[tuple[str, str, bool]]] = {
    "apartment": [
        ("rooms", "Комнат", False),
        ("bedrooms", "Спален", True),
        ("floor", "Этаж", False),
        ("floors_total", "Этажность", False),
        ("building_type", "Тип строения", True),
        ("ceiling_height", "Высота потолков (м)", True),
        ("area_living", "Жилая площадь (м²)", True),
        ("area_kitchen", "Площадь кухни (м²)", True),
        ("condition", "Состояние", False),
        ("bathroom", "Санузел", True),
        ("balcony", "Балкон", True),
        ("furniture", "Мебель", True),
        ("residential_complex", "ЖК (опц.)", True),
        ("internet", "Интернет", True),
    ],
    "house": [
        ("rooms", "Комнат", True),
        ("floors_total", "Этажность", True),
        ("area_living", "Жилая площадь (м²)", True),
        ("area_kitchen", "Площадь кухни (м²)", True),
        ("area_land", "Площадь участка (сотки)", False),
        ("wall_material", "Материал стен", True),
        ("roof_type", "Тип крыши", True),
        ("foundation", "Фундамент", True),
        ("condition", "Состояние", False),
        ("bathroom", "Санузел", True),
        ("furniture", "Мебель", True),
        ("water", "Водоснабжение", True),
        ("sewage", "Канализация", True),
        ("gas", "Газ", True),
        ("electricity", "Электричество", True),
    ],
    "townhouse": [
        ("rooms", "Комнат", True),
        ("floors_total", "Этажность", True),
        ("area_living", "Жилая площадь (м²)", True),
        ("area_land", "Площадь участка (сотки)", True),
        ("condition", "Состояние", False),
        ("wall_material", "Материал стен", True),
        ("bathroom", "Санузел", True),
        ("furniture", "Мебель", True),
        ("water", "Водоснабжение", True),
        ("sewage", "Канализация", True),
        ("gas", "Газ", True),
        ("electricity", "Электричество", True),
    ],
    "commercial": [
        ("commercial_type", "Назначение", False),
        ("floor", "Этаж", True),
        ("floors_total", "Этажность", True),
        ("area_commercial", "Торговая площадь (м²)", True),
        ("area_warehouse", "Складская площадь (м²)", True),
        ("ceiling_height", "Высота потолков (м)", True),
        ("condition", "Состояние", True),
        ("separate_entrance", "Отдельный вход", True),
        ("has_showcase", "Витрины", True),
        ("electricity_power", "Мощность электричества (кВт)", True),
        ("internet", "Интернет", True),
    ],
    "land": [
        ("area_land", "Площадь участка (сотки)", False),
        ("land_category", "Категория земли", False),
        ("land_status", "Статус земли", True),
        ("road_access", "Подъездная дорога", True),
        ("communications_nearby", "Коммуникации рядом", True),
        ("water", "Водоснабжение", True),
        ("sewage", "Канализация", True),
        ("gas", "Газ", True),
        ("electricity", "Электричество", True),
    ],
}


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

        prop_type = property_data.get("property_type", "apartment")
        system_prompt = SCORING_PROMPTS.get(prop_type, SCORING_PROMPTS["apartment"])
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
                    "system": system_prompt,
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
        prop_type = data.get("property_type", "apartment")
        type_fields = PROPERTY_TYPE_FIELDS.get(prop_type, PROPERTY_TYPE_FIELDS["apartment"])
        all_fields = _COMMON_FIELDS + type_fields

        lines = ["Данные объекта недвижимости:"]
        for key, label, optional in all_fields:
            value = data.get(key)
            if value:
                lines.append(f"- {label}: {value}")
            elif not optional:
                lines.append(f"- {label}: не указано")
        return "\n".join(lines)

    def _parse_response(self, api_response: dict[str, Any]) -> dict[str, Any] | None:
        try:
            content = api_response["content"][0]["text"]
            text = content.strip()
            if text.startswith("```"):
                text = text.split("\n", 1)[1] if "\n" in text else text[3:]
                if text.endswith("```"):
                    text = text[:-3]
                text = text.strip()

            result = json.loads(text)

            for key in ("price_score", "quality_score", "listing_score"):
                score = int(result[key])
                result[key] = max(1, min(10, score))

            result["rationale"] = str(result.get("rationale", ""))
            return result
        except (KeyError, IndexError, json.JSONDecodeError, ValueError, TypeError) as exc:
            _logger.error("Failed to parse Anthropic response: %s", exc)
            return None
