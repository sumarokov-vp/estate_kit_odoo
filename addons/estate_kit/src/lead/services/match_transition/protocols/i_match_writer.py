from typing import Any, Protocol


class IMatchWriter(Protocol):
    def write(self, record: Any, vals: dict[str, Any]) -> bool: ...
