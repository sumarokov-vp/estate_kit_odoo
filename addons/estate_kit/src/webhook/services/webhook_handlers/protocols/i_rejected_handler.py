from typing import Any, Protocol


class IRejectedHandler(Protocol):
    def handle(self, payload: dict[str, Any]) -> None: ...
