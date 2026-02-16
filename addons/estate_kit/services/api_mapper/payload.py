import logging
from typing import Any

from .attributes import ATTRIBUTE_FIELD_MAP
from .enum_values import ODOO_TO_API_ENUM_MAP
from .property_types import (
    ODOO_TO_API_DEAL_TYPE,
    ODOO_TO_API_PROPERTY_TYPE,
    ODOO_TO_API_STATE,
)

_logger = logging.getLogger(__name__)


def prepare_api_payload(record: Any, attribute_ids: dict[str, int]) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "property_type_id": ODOO_TO_API_PROPERTY_TYPE.get(record.property_type),
        "deal_type_id": ODOO_TO_API_DEAL_TYPE.get(record.deal_type),
        "status_id": ODOO_TO_API_STATE.get(record.state),
        "price": str(record.price) if record.price else "0",
        "area": str(record.area_total) if record.area_total else "0",
        "description": record.description or "",
    }

    if record.owner_id and record.owner_id.external_owner_id:
        payload["owner_id"] = record.owner_id.external_owner_id

    payload["location"] = _build_location(record)
    payload["attributes"] = _build_attributes(record, attribute_ids)

    return payload


def _build_location(record: Any) -> dict[str, Any]:
    location: dict[str, Any] = {}
    if record.city_id and record.city_id.external_id:
        location["city_id"] = record.city_id.external_id
    if record.district_id and record.district_id.external_id:
        location["district_id"] = record.district_id.external_id
    if record.street_id:
        location["street"] = record.street_id.name
    if record.house_number:
        location["house_number"] = record.house_number
    if record.apartment_number:
        location["apartment_number"] = record.apartment_number
    if record.latitude:
        location["latitude"] = str(record.latitude)
    if record.longitude:
        location["longitude"] = str(record.longitude)
    return location


def _build_attributes(record: Any, attribute_ids: dict[str, int]) -> list[dict[str, Any]]:
    attributes: list[dict[str, Any]] = []

    for odoo_field, (api_name, value_field) in ATTRIBUTE_FIELD_MAP.items():
        attr_id = attribute_ids.get(api_name)
        if not attr_id:
            continue

        value = getattr(record, odoo_field, None)

        if value_field == "value_bool":
            bool_value = bool(value)
            if odoo_field == "not_corner":
                bool_value = not bool_value
            attributes.append({"attribute_id": attr_id, "value_bool": bool_value})

        elif value_field == "value_text":
            if not value:
                continue
            enum_map = ODOO_TO_API_ENUM_MAP.get(odoo_field, {})
            mapped = enum_map.get(value)
            if not mapped:
                continue
            attributes.append({"attribute_id": attr_id, "value_text": mapped})

        elif value_field == "value_int":
            if not value:
                continue
            attributes.append({"attribute_id": attr_id, "value_int": int(value)})

        elif value_field == "value_decimal":
            if not value:
                continue
            attributes.append({"attribute_id": attr_id, "value_decimal": str(value)})

    return attributes
