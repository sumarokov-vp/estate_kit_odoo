from typing import Any

from .field_mapping import _COMMON_FIELDS, PROPERTY_TYPE_FIELDS


class ScoringMessageBuilder:
    def build(self, property_data: dict[str, Any]) -> str:
        prop_type = property_data.get("property_type", "apartment")
        type_fields = PROPERTY_TYPE_FIELDS.get(prop_type, PROPERTY_TYPE_FIELDS["apartment"])
        all_fields = _COMMON_FIELDS + type_fields

        lines = ["Данные объекта недвижимости:"]
        for key, label, optional in all_fields:
            value = property_data.get(key)
            if value:
                lines.append(f"- {label}: {value}")
            elif not optional:
                lines.append(f"- {label}: не указано")
        return "\n".join(lines)
