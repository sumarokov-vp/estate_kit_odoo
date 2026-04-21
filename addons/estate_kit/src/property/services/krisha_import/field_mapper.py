from typing import Any

from .protocols import IBuildingTypeResolver, ICityResolver


class FieldMapper:
    def __init__(
        self,
        city_resolver: ICityResolver,
        building_type_resolver: IBuildingTypeResolver,
    ) -> None:
        self._city_resolver = city_resolver
        self._building_type_resolver = building_type_resolver

    def map(self, detail: dict[str, Any]) -> dict[str, Any]:
        rooms = detail.get("rooms") or 0
        area = detail.get("area") or 0.0
        title = detail.get("title") or ""
        name = title or f"{rooms}-комн. квартира, {area} м²"

        vals: dict[str, Any] = {
            "name": name,
            "property_type": "apartment",
            "deal_type": "sale",
            "state": "imported",
            "rooms": rooms,
            "area_total": area,
            "floor": detail.get("floor"),
            "floors_total": detail.get("floors_total"),
            "price": detail.get("price") or 0,
            "latitude": detail.get("latitude"),
            "longitude": detail.get("longitude"),
            "description": detail.get("description") or "",
            "krisha_url": detail.get("url"),
        }

        city_id = self._city_resolver.resolve(detail.get("city"))
        if city_id:
            vals["city_id"] = city_id

        residential_complex = detail.get("residential_complex")
        if residential_complex:
            vals["residential_complex"] = residential_complex

        year_built = detail.get("year_built")
        if year_built:
            vals["year_built"] = year_built

        ceiling_height = detail.get("ceiling_height")
        if ceiling_height:
            vals["ceiling_height"] = ceiling_height

        building_type = self._building_type_resolver.resolve(detail.get("building_type"))
        if building_type:
            vals["building_type"] = building_type

        return vals
