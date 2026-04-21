from typing import Any, Protocol


class IPropertyCreator(Protocol):
    def create(self, detail: dict[str, Any]) -> int: ...
