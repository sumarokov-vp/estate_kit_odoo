from typing import Any, Protocol


class IPropertyDataFetcher(Protocol):
    def fetch(self, property_id: int) -> dict[str, Any] | None: ...
