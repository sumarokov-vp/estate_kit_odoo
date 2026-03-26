from typing import Any, Protocol


class INewListingHandler(Protocol):
    def handle(self, payload: dict[str, Any]) -> None: ...
