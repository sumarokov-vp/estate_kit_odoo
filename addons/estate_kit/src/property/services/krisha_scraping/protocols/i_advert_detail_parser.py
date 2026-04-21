from typing import Any, Protocol


class IAdvertDetailParser(Protocol):
    def parse(self, html: str) -> dict[str, Any]: ...
