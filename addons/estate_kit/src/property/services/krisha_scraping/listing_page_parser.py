from typing import Any

from bs4 import BeautifulSoup

from .protocols import IHtmlFallbackParser


class ListingPageParser:
    def __init__(self, html_fallback_parser: IHtmlFallbackParser) -> None:
        self._html_fallback_parser = html_fallback_parser

    def parse(self, html: str) -> list[dict[str, Any]]:
        soup = BeautifulSoup(html, "html.parser")
        return self._html_fallback_parser.parse(soup)
