from typing import Any, Protocol

from bs4 import BeautifulSoup


class IHtmlFallbackParser(Protocol):
    def parse(self, soup: BeautifulSoup) -> list[dict[str, Any]]: ...
