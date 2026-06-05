from typing import Protocol


class ISelectionLabeler(Protocol):
    def label(self, prop, field_name: str) -> str | None: ...
