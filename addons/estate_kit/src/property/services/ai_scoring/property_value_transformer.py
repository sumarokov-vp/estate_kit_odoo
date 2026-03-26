from .scoring_data import SELECTION_LABELS


class PropertyValueTransformer:
    def get_value(self, prop, field_name: str):
        raw = getattr(prop, field_name, None)
        if raw is None:
            return None
        if field_name in SELECTION_LABELS:
            return SELECTION_LABELS[field_name].get(raw, raw) if raw else None
        if hasattr(raw, "name"):
            return raw.name if raw else None
        if isinstance(raw, bool):
            return "Да" if raw else None
        return raw or None
