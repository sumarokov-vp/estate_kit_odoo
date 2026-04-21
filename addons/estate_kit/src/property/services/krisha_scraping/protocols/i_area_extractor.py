from typing import Any, Protocol


class IAreaExtractor(Protocol):
    def extract(self, value: Any) -> float: ...
