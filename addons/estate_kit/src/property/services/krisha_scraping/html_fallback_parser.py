import re
from typing import Any

from bs4 import BeautifulSoup

from .config import BASE_URL
from .protocols import IPriceParser, IRoomsExtractor

_AREA_PATTERN = re.compile(r"(\d+(?:[.,]\d+)?)\s*м[²2]")


class HtmlFallbackParser:
    def __init__(
        self,
        rooms_extractor: IRoomsExtractor,
        price_parser: IPriceParser,
    ) -> None:
        self._rooms_extractor = rooms_extractor
        self._price_parser = price_parser

    def parse(self, soup: BeautifulSoup) -> list[dict[str, Any]]:
        items: list[dict[str, Any]] = []
        for card in soup.select("div[data-id]"):
            krisha_id = card.get("data-id")
            if not krisha_id:
                continue

            link = card.select_one("a.a-card__title")
            title = link.get_text(strip=True) if link else ""
            href = link.get("href", "") if link else ""

            price_el = card.select_one(".a-card__price")
            price_text = price_el.get_text(strip=True) if price_el else "0"
            price = self._price_parser.parse(price_text)

            area_match = _AREA_PATTERN.search(title)
            try:
                area = float(area_match.group(1).replace(",", ".")) if area_match else 0.0
            except ValueError:
                area = 0.0

            items.append({
                "krisha_id": int(krisha_id if isinstance(krisha_id, str) else krisha_id[0]),
                "url": f"{BASE_URL}{href}" if href else f"{BASE_URL}/a/show/{krisha_id}",
                "title": title,
                "rooms": self._rooms_extractor.extract(title),
                "area": area,
                "floor": None,
                "floors_total": None,
                "price": price,
                "city": "",
                "address": "",
                "latitude": None,
                "longitude": None,
                "description": "",
                "photo_urls": [],
            })

        return items
