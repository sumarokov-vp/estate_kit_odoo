from typing import Any, Protocol

from bs4 import BeautifulSoup


class IResidentialComplexHtmlExtractor(Protocol):
    def extract(self, soup: BeautifulSoup) -> dict[str, Any]: ...
