from typing import Any, Protocol


class IContactRequestHandler(Protocol):
    def handle(self, payload: dict[str, Any]) -> None: ...
