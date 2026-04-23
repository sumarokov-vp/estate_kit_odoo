from typing import Any, Protocol


class IListingFetcher(Protocol):
    def fetch(self, url: str, page: int) -> list[dict[str, Any]]: ...
