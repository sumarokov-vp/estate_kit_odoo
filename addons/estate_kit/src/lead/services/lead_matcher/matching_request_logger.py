from typing import Any

from ..matching_client import SearchCriteria

_LOG_CATEGORY = "matching"

_FIELD_LABELS = [
    ("deal_type", "тип сделки"),
    ("property_type", "тип"),
    ("city", "город"),
]

_RANGE_LABELS = [
    ("rooms_min", "rooms_max", "комнат"),
    ("price_min", "price_max", "цена"),
    ("area_min", "area_max", "площадь"),
]


class MatchingRequestLogger:
    def log(self, Log: Any, lead_id: int, criteria: SearchCriteria) -> None:
        parts: list[str] = []
        for attr, label in _FIELD_LABELS:
            value = getattr(criteria, attr)
            if value:
                parts.append("%s=%s" % (label, value))
        if criteria.districts:
            parts.append("районы=%s" % ", ".join(criteria.districts))
        for attr_min, attr_max, label in _RANGE_LABELS:
            v_min = getattr(criteria, attr_min)
            v_max = getattr(criteria, attr_max)
            if v_min is not None and v_max is not None:
                parts.append("%s %s–%s" % (label, v_min, v_max))
            elif v_min is not None:
                parts.append("%s от %s" % (label, v_min))
            elif v_max is not None:
                parts.append("%s до %s" % (label, v_max))

        Log.log(
            _LOG_CATEGORY,
            "Запрос подбора для лида #%d" % lead_id,
            details=", ".join(parts) if parts else "без критериев",
        )
