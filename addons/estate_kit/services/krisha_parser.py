import json
import logging
import re
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlencode

import requests
from bs4 import BeautifulSoup

_logger = logging.getLogger(__name__)

BASE_URL = "https://krisha.kz"
SEARCH_URL = f"{BASE_URL}/prodazha/kvartiry/"


@dataclass
class KrishaProperty:
    krisha_id: int
    url: str
    title: str
    rooms: int
    area: float
    floor: int
    floors_total: int
    price: int
    city: str
    address: str
    latitude: float | None
    longitude: float | None
    description: str
    photo_urls: list[str]


@dataclass
class ParseParams:
    city: str = "almaty"
    rooms: str = ""
    price_from: int = 0
    price_to: int = 0
    has_photo: bool = True
    owner: bool = False


class KrishaParser:
    def __init__(self, timeout: int = 30):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
        })
        self.timeout = timeout

    def build_search_url(self, params: ParseParams, page: int = 1) -> str:
        city_url = f"{BASE_URL}/prodazha/kvartiry/{params.city}/"

        query_params: dict[str, Any] = {}

        if params.rooms:
            query_params["das[live.rooms]"] = params.rooms

        if params.price_from:
            query_params["das[price][from]"] = params.price_from

        if params.price_to:
            query_params["das[price][to]"] = params.price_to

        if params.has_photo:
            query_params["das[_sys.hasphoto]"] = 1

        if params.owner:
            query_params["das[who]"] = 1

        if page > 1:
            query_params["page"] = page

        if query_params:
            return f"{city_url}?{urlencode(query_params)}"
        return city_url

    def parse_listing_page(self, html: str) -> list[dict[str, Any]]:
        soup = BeautifulSoup(html, "html.parser")
        items: list[dict[str, Any]] = []

        script_tag = soup.find("script", {"id": "jsdata"})
        if script_tag and script_tag.string:
            try:
                # Try both old and new formats
                match = re.search(r"window\.(?:__DATA__|data)\s*=\s*(\{.+\})", script_tag.string)
                if match:
                    data = json.loads(match.group(1))
                    adverts = data.get("adverts", [])
                    for advert in adverts:
                        items.append(self._parse_advert(advert))
            except (json.JSONDecodeError, KeyError) as e:
                _logger.warning("Failed to parse jsdata: %s", e)

        if not items:
            items = self._parse_html_fallback(soup)

        return items

    def _parse_advert(self, advert: dict[str, Any]) -> dict[str, Any]:
        photos = advert.get("photos", [])
        photo_urls = [
            photo.get("src", "").replace("-thumb", "-full")
            for photo in photos
            if photo.get("src")
        ]

        map_data = advert.get("map", {})
        lat = map_data.get("lat")
        lon = map_data.get("lon")

        return {
            "krisha_id": advert.get("id"),
            "url": f"{BASE_URL}/a/show/{advert.get('id')}",
            "title": advert.get("title", ""),
            "rooms": self._extract_rooms(advert.get("title", "")),
            "area": self._extract_area(advert.get("square")),
            "floor": advert.get("floor"),
            "floors_total": advert.get("floorCount"),
            "price": advert.get("price"),
            "city": advert.get("city", {}).get("title", ""),
            "address": advert.get("address", ""),
            "latitude": float(lat) if lat else None,
            "longitude": float(lon) if lon else None,
            "description": "",
            "photo_urls": photo_urls,
        }

    def _parse_html_fallback(self, soup: BeautifulSoup) -> list[dict[str, Any]]:
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
            price = self._parse_price(price_text)

            items.append({
                "krisha_id": int(krisha_id),
                "url": f"{BASE_URL}{href}" if href else f"{BASE_URL}/a/show/{krisha_id}",
                "title": title,
                "rooms": self._extract_rooms(title),
                "area": 0.0,
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

    def fetch_page(self, url: str) -> str:
        response = self.session.get(url, timeout=self.timeout)
        response.raise_for_status()
        return response.text

    def fetch_property_details(self, url: str) -> dict[str, Any]:
        _logger.info("Fetching details from: %s", url)
        try:
            html = self.fetch_page(url)
            soup = BeautifulSoup(html, "html.parser")

            script_tag = soup.find("script", {"id": "jsdata"})
            _logger.info("Script tag found: %s, has string: %s", script_tag is not None, script_tag.string is not None if script_tag else False)

            if script_tag and script_tag.string:
                # Try both old and new formats
                match = re.search(r"window\.(?:__DATA__|data)\s*=\s*(\{.+\})", script_tag.string)
                if match:
                    data = json.loads(match.group(1))
                    advert = data.get("advert", {})
                    result = self._parse_detail_advert(advert)
                    _logger.info("Parsed details: %d photos found", len(result.get("photo_urls", [])))
                    return result
                else:
                    _logger.warning("Regex did not match __DATA__")
            else:
                _logger.warning("No jsdata script found or empty string")
        except Exception as e:
            _logger.exception("Error fetching details: %s", e)

        return {}

    def _parse_detail_advert(self, advert: dict[str, Any]) -> dict[str, Any]:
        photos = advert.get("photos", [])
        photo_urls = [
            photo.get("src", "").replace("-thumb", "-full")
            for photo in photos
            if photo.get("src")
        ]

        map_data = advert.get("map", {})
        lat = map_data.get("lat")
        lon = map_data.get("lon")

        return {
            "krisha_id": advert.get("id"),
            "url": f"{BASE_URL}/a/show/{advert.get('id')}",
            "title": advert.get("title", ""),
            "rooms": self._extract_rooms(advert.get("title", "")),
            "area": self._extract_area(advert.get("square")),
            "floor": advert.get("floor"),
            "floors_total": advert.get("floorCount"),
            "price": advert.get("price"),
            "city": advert.get("city", {}).get("title", ""),
            "address": advert.get("addressTitle", "") or advert.get("address", ""),
            "latitude": float(lat) if lat else None,
            "longitude": float(lon) if lon else None,
            "description": advert.get("text", ""),
            "photo_urls": photo_urls,
        }

    def parse(self, params: ParseParams, max_pages: int = 1) -> list[dict[str, Any]]:
        all_items: list[dict[str, Any]] = []

        for page in range(1, max_pages + 1):
            url = self.build_search_url(params, page)
            _logger.info("Parsing page %d: %s", page, url)

            try:
                html = self.fetch_page(url)
                items = self.parse_listing_page(html)

                if not items:
                    _logger.info("No items found on page %d, stopping", page)
                    break

                all_items.extend(items)
                _logger.info("Found %d items on page %d", len(items), page)

            except requests.RequestException as e:
                _logger.exception("Failed to fetch page %d: %s", page, e)
                break

        return all_items

    def _extract_rooms(self, title: str) -> int:
        match = re.search(r"(\d+)-комн", title)
        if match:
            return int(match.group(1))
        return 0

    def _extract_area(self, value: Any) -> float:
        if isinstance(value, (int, float)):
            return float(value)
        if isinstance(value, str):
            match = re.search(r"(\d+(?:\.\d+)?)", value)
            if match:
                return float(match.group(1))
        return 0.0

    def _parse_price(self, text: str) -> int:
        digits = re.sub(r"\D", "", text)
        return int(digits) if digits else 0

    def download_image(self, url: str) -> bytes | None:
        try:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            return response.content
        except requests.RequestException as e:
            _logger.warning("Failed to download image %s: %s", url, e)
            return None
