from typing import Any, Protocol


class IListingRemovedHandler(Protocol):
    def handle(self, payload: dict[str, Any]) -> None: ...
