from typing import Any, Protocol


class IStatusChecker(Protocol):
    def check(self, settings: Any) -> dict: ...
