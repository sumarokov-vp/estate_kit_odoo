import re
from typing import Any

from bs4 import BeautifulSoup

_FLOOR_RE = re.compile(r"(\d+)\s*из\s*(\d+)")
_FLOOR_SLASH_RE = re.compile(r"(\d+)\s*/\s*(\d+)\s*этаж")
_YEAR_RE = re.compile(r"\d{4}")
_FLOAT_RE = re.compile(r"\d+(?:[.,]\d+)?")


class AdvertInfoHtmlExtractor:
    def extract(self, soup: BeautifulSoup) -> dict[str, Any]:
        result: dict[str, Any] = {}

        for item in soup.select("div.offer__info-item[data-name]"):
            raw_name = item.get("data-name")
            name = raw_name if isinstance(raw_name, str) else ""
            value_node = item.select_one(".offer__advert-short-info")
            if not value_node:
                continue
            value = value_node.get_text(" ", strip=True)
            if not value:
                continue

            if name == "flat.building":
                result["building_type"] = value
            elif name == "house.year":
                match = _YEAR_RE.search(value)
                if match:
                    result["year_built"] = int(match.group(0))
            elif name == "flat.floor":
                match = _FLOOR_RE.search(value)
                if match:
                    result["floor"] = int(match.group(1))
                    result["floors_total"] = int(match.group(2))
                else:
                    single = re.search(r"\d+", value)
                    if single:
                        result["floor"] = int(single.group(0))

        if "floor" not in result or "floors_total" not in result:
            title_node = soup.select_one(".offer__advert-title, h1")
            if title_node:
                title_text = title_node.get_text(" ", strip=True)
                match = _FLOOR_SLASH_RE.search(title_text)
                if match:
                    result.setdefault("floor", int(match.group(1)))
                    result.setdefault("floors_total", int(match.group(2)))

        for dl in soup.select(".offer__parameters dl"):
            dt = dl.find("dt")
            dd = dl.find("dd")
            if not dt or not dd:
                continue
            raw_data_name = dt.get("data-name")
            data_name = raw_data_name.strip() if isinstance(raw_data_name, str) else ""
            title_text = dt.get_text(" ", strip=True)
            value_text = dd.get_text(" ", strip=True)
            if not value_text:
                continue
            if data_name == "ceiling" or title_text.lower().startswith("высота потолков"):
                match = _FLOAT_RE.search(value_text)
                if match:
                    result["ceiling_height"] = float(match.group(0).replace(",", "."))

        return result
