from typing import Any

from ..krisha_scraping.protocols import IHttpFetcher, IListingPageParser


class ListingFetcher:
    def __init__(
        self,
        http_fetcher: IHttpFetcher,
        page_parser: IListingPageParser,
    ) -> None:
        self._http_fetcher = http_fetcher
        self._page_parser = page_parser

    def fetch(self, url: str, limit: int) -> list[dict[str, Any]]:
        html = self._http_fetcher.fetch(url)
        items = self._page_parser.parse(html)
        return items[:limit] if limit > 0 else items
