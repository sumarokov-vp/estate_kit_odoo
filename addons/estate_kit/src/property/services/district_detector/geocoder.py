import logging

import requests

_logger = logging.getLogger(__name__)

TWOGIS_GEOCODE_URL = "https://catalog.api.2gis.com/3.0/items/geocode"
DISTRICT_MARKER = "район"
RESIDENTIAL_MARKER = "жилой"


class TwoGisGeocoder:
    def __init__(self, env):
        icp = env["ir.config_parameter"].sudo()
        self.api_key = icp.get_param("estate_kit.twogis_api_key") or ""

    @property
    def is_configured(self) -> bool:
        return bool(self.api_key)

    def geocode_address(self, address):
        response = requests.get(
            TWOGIS_GEOCODE_URL,
            params={
                "key": self.api_key,
                "q": address,
                "fields": "items.point",
            },
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()

        items = data.get("result", {}).get("items", [])
        if not items:
            return None

        point = items[0].get("point") or {}
        lat = point.get("lat")
        lon = point.get("lon")
        if lat is None or lon is None:
            return None
        return float(lat), float(lon)

    def reverse_geocode_district(self, lat, lon):
        response = requests.get(
            TWOGIS_GEOCODE_URL,
            params={
                "key": self.api_key,
                "lat": lat,
                "lon": lon,
                "fields": "items.adm_div",
                "type": "adm_div.district,adm_div.city,adm_div.settlement,building",
            },
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()

        items = data.get("result", {}).get("items", [])
        for item in items:
            for division in item.get("adm_div", []) or []:
                name = division.get("name", "") or ""
                normalized = name.lower()
                if DISTRICT_MARKER in normalized and RESIDENTIAL_MARKER not in normalized:
                    return name

        for item in items:
            if item.get("subtype") == "district":
                name = item.get("name", "") or ""
                normalized = name.lower()
                if DISTRICT_MARKER in normalized and RESIDENTIAL_MARKER not in normalized:
                    return name

        return None

    def find_or_create_district(self, env, lat: float, lon: float, city_id: int):
        district_name = self.reverse_geocode_district(lat, lon)
        if not district_name:
            _logger.warning("Район не найден для координат: %s, %s", lat, lon)
            return None
        district = env["estate.district"].search(
            [("name", "ilike", district_name), ("city_id", "=", city_id)],
            limit=1,
        )
        if not district:
            district = env["estate.district"].create(
                {"name": district_name, "city_id": city_id}
            )
        return district
