from typing import Any, Protocol


class IRegistrator(Protocol):
    def register(self, settings: Any) -> dict: ...
