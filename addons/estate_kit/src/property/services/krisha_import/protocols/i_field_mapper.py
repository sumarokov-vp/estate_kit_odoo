from typing import Any, Protocol


class IFieldMapper(Protocol):
    def map(self, detail: dict[str, Any]) -> dict[str, Any]: ...
