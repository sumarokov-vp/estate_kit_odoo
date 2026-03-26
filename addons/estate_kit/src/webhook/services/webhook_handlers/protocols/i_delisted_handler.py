from typing import Any, Protocol


class IDelistedHandler(Protocol):
    def handle(self, payload: dict[str, Any]) -> None: ...
