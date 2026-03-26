from typing import Any, Callable, Protocol


class IHandlerRegistry(Protocol):
    def get_handler(self, event_type: str) -> Callable[[dict[str, Any]], None] | None: ...
