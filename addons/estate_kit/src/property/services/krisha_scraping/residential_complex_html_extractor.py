from typing import Any

from bs4 import BeautifulSoup

from .config import BASE_URL


class ResidentialComplexHtmlExtractor:
    def extract(self, soup: BeautifulSoup) -> dict[str, Any]:
        for title in soup.select("div.offer__info-title"):
            if title.get_text(strip=True) != "Жилой комплекс":
                continue
            info = title.find_next("div", class_="offer__advert-short-info")
            if not info:
                continue
            link = info.find("a")
            if link:
                name = link.get_text(strip=True)
                href = link.get("href", "")
                href_str = href if isinstance(href, str) else (href[0] if href else "")
                url = f"{BASE_URL}{href_str}" if href_str and href_str.startswith("/") else href_str or None
                return {"name": name, "krisha_url": url}
            name = info.get_text(strip=True)
            if name:
                return {"name": name, "krisha_url": None}
        return {}
