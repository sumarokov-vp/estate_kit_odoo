from typing import Any, Protocol

from bs4 import BeautifulSoup


class IAdvertInfoHtmlExtractor(Protocol):
    def extract(self, soup: BeautifulSoup) -> dict[str, Any]: ...
