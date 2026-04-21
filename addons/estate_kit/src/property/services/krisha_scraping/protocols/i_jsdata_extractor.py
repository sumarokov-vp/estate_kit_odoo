from typing import Any, Protocol


class IJsdataExtractor(Protocol):
    def extract(self, html: str) -> dict[str, Any] | None: ...
