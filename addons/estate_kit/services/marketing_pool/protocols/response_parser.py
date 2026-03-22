from typing import Any, Protocol


class IResponseParser(Protocol):
    def parse(self, response_text: str) -> dict[str, Any] | None: ...
