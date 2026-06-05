from .metrics_layout import UTILITY_FIELDS
from .protocols import ISelectionLabeler


class MetricValueResolver:
    def __init__(self, selection_labeler: ISelectionLabeler) -> None:
        self._selection_labeler = selection_labeler

    def resolve(self, prop, spec) -> str | None:
        kind = spec[0]
        if kind == "number":
            raw = getattr(prop, spec[2], 0)
            return f"{raw:g}{spec[3]}" if raw else None
        if kind == "int":
            raw = getattr(prop, spec[2], 0)
            return str(raw) if raw else None
        if kind == "floor":
            if not (prop.floor or prop.floors_total):
                return None
            return f"{prop.floor or '—'} / {prop.floors_total or '—'}"
        if kind == "selection":
            return self._selection_labeler.label(prop, spec[2])
        if kind == "utilities":
            present = any(getattr(prop, field, False) for field in UTILITY_FIELDS)
            return "Есть" if present else None
        return None
