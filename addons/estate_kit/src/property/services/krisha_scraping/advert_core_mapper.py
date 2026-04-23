from typing import Any

from .config import BASE_URL
from .protocols import IAreaExtractor, IRoomsExtractor


class AdvertCoreMapper:
    def __init__(
        self,
        rooms_extractor: IRoomsExtractor,
        area_extractor: IAreaExtractor,
    ) -> None:
        self._rooms_extractor = rooms_extractor
        self._area_extractor = area_extractor

    def map(self, advert: dict[str, Any]) -> dict[str, Any]:
        photo_urls = [
            photo.get("src", "").replace("-thumb", "-full")
            for photo in advert.get("photos", [])
            if photo.get("src")
        ]

        map_data = advert.get("map", {})
        lat = map_data.get("lat")
        lon = map_data.get("lon")

        year_built = advert.get("buildYear") or advert.get("yearBuilt")
        building_type = (
            advert.get("houseType")
            or advert.get("buildingType")
            or advert.get("wallsType")
        )
        ceiling_height = advert.get("ceilingHeight") or advert.get("ceiling")
        krisha_complex_id = advert.get("complexId")

        title = advert.get("title", "")

        return {
            "krisha_id": advert.get("id"),
            "url": f"{BASE_URL}/a/show/{advert.get('id')}",
            "title": title,
            "rooms": self._rooms_extractor.extract(title),
            "area": self._area_extractor.extract(advert.get("square")),
            "floor": advert.get("floor"),
            "floors_total": advert.get("floorCount"),
            "price": advert.get("price"),
            "city": advert.get("city", {}).get("title", ""),
            "latitude": float(lat) if lat else None,
            "longitude": float(lon) if lon else None,
            "photo_urls": photo_urls,
            "year_built": int(year_built) if year_built else None,
            "building_type": building_type if isinstance(building_type, str) else None,
            "ceiling_height": float(ceiling_height) if ceiling_height else None,
            "krisha_complex_id": int(krisha_complex_id) if krisha_complex_id else None,
        }
