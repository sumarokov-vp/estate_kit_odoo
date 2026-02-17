import logging
from typing import Any, Protocol

from .attributes import ATTRIBUTE_FIELD_MAP
from .enum_values import ODOO_TO_API_ENUM_MAP
from .property_types import (
    ODOO_TO_API_DEAL_TYPE,
    ODOO_TO_API_PROPERTY_TYPE,
)

_logger = logging.getLogger(__name__)


class _RelatedWithName(Protocol):
    name: str


class _OwnerLike(Protocol):
    name: str | None
    phone: str | None


class EstatePropertyLike(Protocol):
    property_type: str
    deal_type: str
    price: float
    description: str | None
    owner_id: _OwnerLike | None
    city_id: _RelatedWithName | None
    district_id: _RelatedWithName | None
    street_id: _RelatedWithName | None
    house_number: str | None
    apartment_number: str | None
    residential_complex: str | None
    latitude: float | None
    longitude: float | None


def prepare_api_payload(record: EstatePropertyLike) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "property_type": ODOO_TO_API_PROPERTY_TYPE.get(record.property_type),
        "deal_type": ODOO_TO_API_DEAL_TYPE.get(record.deal_type),
        "price": float(record.price) if record.price else 0,
        "description": record.description or "",
    }

    if record.owner_id:
        partner = record.owner_id
        payload["owner"] = {
            "name": partner.name or "",
            "phone": partner.phone or "",
            "notes": "",
        }

    payload["location"] = _build_location(record)
    payload["attributes"] = _build_attributes(record)

    return payload


def _build_location(record: EstatePropertyLike) -> dict[str, Any]:
    location: dict[str, Any] = {}
    if record.city_id:
        location["city"] = record.city_id.name
    if record.district_id:
        location["district"] = record.district_id.name
    if record.street_id:
        location["street"] = record.street_id.name
    if record.house_number:
        location["house_number"] = record.house_number
    if record.residential_complex:
        location["residential_complex"] = record.residential_complex
    if record.apartment_number:
        location["apartment_number"] = record.apartment_number
    if record.latitude:
        location["latitude"] = str(record.latitude)
    if record.longitude:
        location["longitude"] = str(record.longitude)
    return location


def _build_attributes(record: EstatePropertyLike) -> dict[str, str]:
    attributes: dict[str, str] = {}

    for odoo_field, api_name in ATTRIBUTE_FIELD_MAP.items():
        value = getattr(record, odoo_field, None)
        if value is None:
            continue

        if isinstance(value, bool):
            bool_value = value
            if odoo_field == "not_corner":
                bool_value = not bool_value
            attributes[api_name] = "true" if bool_value else "false"

        elif odoo_field in ODOO_TO_API_ENUM_MAP:
            if not value:
                continue
            mapped = ODOO_TO_API_ENUM_MAP[odoo_field].get(value)
            if mapped:
                attributes[api_name] = str(mapped)

        else:
            if not value:
                continue
            attributes[api_name] = str(value)

    return attributes
