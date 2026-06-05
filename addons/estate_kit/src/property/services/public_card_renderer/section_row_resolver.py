from .protocols import ISelectionLabeler


class SectionRowResolver:
    def __init__(self, selection_labeler: ISelectionLabeler) -> None:
        self._selection_labeler = selection_labeler

    def resolve(self, prop, spec) -> tuple[str, str] | None:
        kind = spec[0]
        if kind == "number":
            field, label, suffix = spec[1], spec[2], spec[3]
            raw = getattr(prop, field, 0)
            return (label, f"{raw:g}{suffix}") if raw else None
        if kind == "int":
            field, label = spec[1], spec[2]
            raw = getattr(prop, field, 0)
            return (label, str(raw)) if raw else None
        if kind == "floor":
            label = spec[1]
            if not (prop.floor or prop.floors_total):
                return None
            return (label, f"{prop.floor or '—'} / {prop.floors_total or '—'}")
        if kind == "selection":
            field, label = spec[1], spec[2]
            value = self._selection_labeler.label(prop, field)
            return (label, value) if value else None
        if kind == "bool":
            field, label = spec[1], spec[2]
            return (label, "Да") if getattr(prop, field, False) else None
        return None
