from .protocols import ISelectionLabeler


class TypeLabelResolver:
    def __init__(self, selection_labeler: ISelectionLabeler) -> None:
        self._selection_labeler = selection_labeler

    def resolve(self, prop) -> str:
        return self._selection_labeler.label(prop, "property_type") or ""
