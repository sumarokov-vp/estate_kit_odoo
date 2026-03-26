from typing import Any, Protocol


class IPropertyFinder(Protocol):
    def find(self, payload: dict[str, Any], event_name: str) -> tuple[int | None, Any]: ...
