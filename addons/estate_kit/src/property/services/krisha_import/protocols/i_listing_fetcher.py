from typing import Any, Protocol


class IListingFetcher(Protocol):
    def fetch(self, url: str) -> list[dict[str, Any]]: ...
