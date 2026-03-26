from typing import Any, Protocol


class ITransitionHandler(Protocol):
    def handle(self, payload: dict[str, Any]) -> None: ...
