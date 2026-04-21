from typing import Any, Protocol


class IListingPageParser(Protocol):
    def parse(self, html: str) -> list[dict[str, Any]]: ...
