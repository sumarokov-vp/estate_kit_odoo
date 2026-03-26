from typing import Any, Protocol


class IApprovedHandler(Protocol):
    def handle(self, payload: dict[str, Any]) -> None: ...
