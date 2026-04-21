from typing import Any, Protocol


class IListingFetcher(Protocol):
    def fetch(self, url: str, limit: int) -> list[dict[str, Any]]: ...
