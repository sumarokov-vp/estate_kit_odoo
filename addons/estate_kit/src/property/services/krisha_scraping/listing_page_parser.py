from typing import Any

from bs4 import BeautifulSoup

from .protocols import (
    IHtmlFallbackParser,
    IJsdataExtractor,
    IListingAdvertMapper,
)


class ListingPageParser:
    def __init__(
        self,
        jsdata_extractor: IJsdataExtractor,
        advert_mapper: IListingAdvertMapper,
        html_fallback_parser: IHtmlFallbackParser,
    ) -> None:
        self._jsdata_extractor = jsdata_extractor
        self._advert_mapper = advert_mapper
        self._html_fallback_parser = html_fallback_parser

    def parse(self, html: str) -> list[dict[str, Any]]:
        items: list[dict[str, Any]] = []

        data = self._jsdata_extractor.extract(html)
        if data:
            for advert in data.get("adverts", []):
                items.append(self._advert_mapper.map(advert))

        if not items:
            soup = BeautifulSoup(html, "html.parser")
            items = self._html_fallback_parser.parse(soup)

        return items
