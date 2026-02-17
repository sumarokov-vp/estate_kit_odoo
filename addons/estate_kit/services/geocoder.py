import logging

import requests

_logger = logging.getLogger(__name__)

YANDEX_GEOCODER_URL = "https://geocode-maps.yandex.ru/1.x/"
DISTRICT_MARKER = "район"
RESIDENTIAL_MARKER = "жилой"


class YandexGeocoder:
    def __init__(self, env):
        self.api_key = (
            env["ir.config_parameter"]
            .sudo()
            .get_param("estate_kit.yandex_geocoder_api_key")
        ) or ""

    @property
    def is_configured(self) -> bool:
        return bool(self.api_key)

    def geocode_address(self, address):
        response = requests.get(
            YANDEX_GEOCODER_URL,
            params={"apikey": self.api_key, "geocode": address, "format": "json"},
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()

        feature_members = (
            data.get("response", {})
            .get("GeoObjectCollection", {})
            .get("featureMember", [])
        )
        if not feature_members:
            return None

        geo_object = feature_members[0].get("GeoObject", {})
        pos = geo_object.get("Point", {}).get("pos", "")
        if not pos:
            return None

        lon, lat = pos.split()
        return float(lat), float(lon)

    def reverse_geocode_district(self, lat, lon):
        response = requests.get(
            YANDEX_GEOCODER_URL,
            params={
                "apikey": self.api_key,
                "geocode": f"{lon},{lat}",
                "format": "json",
                "kind": "district",
            },
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()

        feature_members = (
            data.get("response", {})
            .get("GeoObjectCollection", {})
            .get("featureMember", [])
        )

        for feature in feature_members:
            name = feature.get("GeoObject", {}).get("name", "")
            if DISTRICT_MARKER in name.lower() and RESIDENTIAL_MARKER not in name.lower():
                return name

        for feature in feature_members:
            components = (
                feature.get("GeoObject", {})
                .get("metaDataProperty", {})
                .get("GeocoderMetaData", {})
                .get("Address", {})
                .get("Components", [])
            )
            for comp in components:
                if comp.get("kind") == "district":
                    name = comp.get("name", "")
                    if DISTRICT_MARKER in name.lower() and RESIDENTIAL_MARKER not in name.lower():
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
