import logging

import requests

_logger = logging.getLogger(__name__)

YANDEX_GEOCODER_URL = "https://geocode-maps.yandex.ru/1.x/"


def geocode_address(api_key, address):
    response = requests.get(
        YANDEX_GEOCODER_URL,
        params={"apikey": api_key, "geocode": address, "format": "json"},
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


def reverse_geocode_district(api_key, lat, lon):
    response = requests.get(
        YANDEX_GEOCODER_URL,
        params={
            "apikey": api_key,
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
        if "район" in name.lower() and "жилой" not in name.lower():
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
                if "район" in name.lower() and "жилой" not in name.lower():
                    return name

    return None
