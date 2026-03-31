from typing import Any, Protocol


class IMatchRecord(Protocol):
    def write(self, vals: dict[str, Any]) -> bool: ...

    def filtered(self, func: Any) -> "IMatchRecord": ...
