from typing import Any

from ..krisha_parser import KrishaParser


class ListingFetcher:
    def __init__(self, parser: KrishaParser) -> None:
        self._parser = parser

    def fetch(self, url: str, limit: int) -> list[dict[str, Any]]:
        html = self._parser.fetch_page(url)
        items = self._parser.parse_listing_page(html)
        return items[:limit] if limit > 0 else items
