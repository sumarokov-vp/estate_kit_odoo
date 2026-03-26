from ..marketing_pool import _COMMON_FIELDS, PROPERTY_TYPE_FIELDS

_LOG_CATEGORY = "ai_scoring"


class ScoringRequestLogger:
    def __init__(self, marketing_pool) -> None:
        self._marketing_pool = marketing_pool

    def log_request(self, Log, prop, property_data: dict) -> None:
        detail_parts = [
            "model=%s" % self._marketing_pool.model,
            "промпт=%s" % prop.property_type,
        ]
        all_fields = _COMMON_FIELDS + PROPERTY_TYPE_FIELDS.get(prop.property_type, [])
        for key, label, _optional in all_fields:
            value = property_data.get(key)
            if value:
                detail_parts.append("%s=%s" % (label, value))
        Log.log(
            _LOG_CATEGORY,
            "Запрос AI-скоринга: %s [%s]" % (prop.name, prop.property_type),
            details=", ".join(detail_parts),
            property_id=prop.id,
        )
