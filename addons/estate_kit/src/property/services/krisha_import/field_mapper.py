from typing import Any

from .protocols import (
    IAddressParser,
    IBuildingTypeResolver,
    ICityResolver,
    IResidentialComplexResolver,
    IStreetResolver,
)


class FieldMapper:
    def __init__(
        self,
        city_resolver: ICityResolver,
        building_type_resolver: IBuildingTypeResolver,
        residential_complex_resolver: IResidentialComplexResolver,
        street_resolver: IStreetResolver,
        address_parser: IAddressParser,
    ) -> None:
        self._city_resolver = city_resolver
        self._building_type_resolver = building_type_resolver
        self._residential_complex_resolver = residential_complex_resolver
        self._street_resolver = street_resolver
        self._address_parser = address_parser

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

        complex_id = self._residential_complex_resolver.resolve(
            detail.get("krisha_complex_id"),
            detail.get("residential_complex_name"),
            detail.get("residential_complex_krisha_url"),
            city_id,
        )
        if complex_id:
            vals["residential_complex_id"] = complex_id

        year_built = detail.get("year_built")
        if year_built:
            vals["year_built"] = year_built

        ceiling_height = detail.get("ceiling_height")
        if ceiling_height:
            vals["ceiling_height"] = ceiling_height

        building_type = self._building_type_resolver.resolve(detail.get("building_type"))
        if building_type:
            vals["building_type"] = building_type

        address_title = detail.get("address_title") or detail.get("address") or ""
        address_struct = detail.get("address_struct") or {}

        street_name, house_from_title = self._address_parser.parse(address_title)

        house_number = (
            address_struct.get("house_num")
            if isinstance(address_struct, dict)
            else None
        ) or house_from_title
        if house_number:
            vals["house_number"] = house_number

        if street_name and city_id:
            street_id = self._street_resolver.resolve(street_name, city_id)
            if street_id:
                vals["street_id"] = street_id

        return vals
