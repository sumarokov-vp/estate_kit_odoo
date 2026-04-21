from typing import Any

from ..krisha_scraping.protocols import IHttpFetcher, IListingPageParser
from .protocols import IPageUrlBuilder


class ListingFetcher:
    def __init__(
        self,
        http_fetcher: IHttpFetcher,
        page_parser: IListingPageParser,
        page_url_builder: IPageUrlBuilder,
    ) -> None:
        self._http_fetcher = http_fetcher
        self._page_parser = page_parser
        self._page_url_builder = page_url_builder

    def fetch(self, url: str, page: int) -> list[dict[str, Any]]:
        page_url = self._page_url_builder.build(url, page)
        html = self._http_fetcher.fetch(page_url)
        return self._page_parser.parse(html)
