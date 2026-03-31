from typing import Any, Protocol


class ILeadRecord(Protocol):
    def write(self, vals: dict[str, Any]) -> bool: ...
