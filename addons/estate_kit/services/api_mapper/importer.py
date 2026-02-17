import logging
from typing import Any

from .property_types import API_PROPERTY_TYPE_MAP, PROPERTY_TYPE_LABELS

_logger = logging.getLogger(__name__)

API_DEAL_TYPE_MAP = {
    1: "sale",
    2: "rent_long",
    3: "rent_daily",
}

API_STATE_MAP = {
    1: "draft",
    2: "internal_review",
    3: "active",
    4: "moderation",
    5: "legal_review",
    6: "published",
    7: "rejected",
    8: "unpublished",
    9: "sold",
    10: "archived",
    11: "mls_listed",
    12: "mls_removed",
    13: "mls_sold",
}


def find_or_create_owner(env, owner_data: dict[str, Any]) -> int | None:
    if not owner_data or not owner_data.get("id"):
        return None
    external_id = owner_data["id"]
    partner = env["res.partner"].search(
        [("external_owner_id", "=", external_id)], limit=1
    )
    vals = {
        "name": owner_data.get("name", ""),
        "phone": owner_data.get("phone", ""),
        "external_owner_id": external_id,
    }
    if partner:
        partner.write({"name": vals["name"], "phone": vals["phone"]})
        return partner.id
    return env["res.partner"].create(vals).id


def import_from_api_data(env, data: dict[str, Any]) -> dict[str, Any]:
    vals: dict[str, Any] = {}

    property_type = API_PROPERTY_TYPE_MAP.get(data.get("property_type_id"))
    if property_type:
        vals["property_type"] = property_type

    deal_type = API_DEAL_TYPE_MAP.get(data.get("deal_type_id"))
    if deal_type:
        vals["deal_type"] = deal_type

    state = API_STATE_MAP.get(data.get("status_id"))
    if state:
        vals["state"] = state

    if data.get("description"):
        vals["description"] = data["description"]

    if data.get("price") is not None:
        vals["price"] = float(data["price"])

    if data.get("area") is not None:
        vals["area_total"] = float(data["area"])

    if data.get("owner_name"):
        vals["owner_name"] = data["owner_name"]

    owner_data = {
        "id": data.get("owner_id"),
        "name": data.get("owner_name", ""),
        "phone": data.get("owner_phone", ""),
    }
    owner_id = find_or_create_owner(env, owner_data)
    if owner_id:
        vals["owner_id"] = owner_id

    location = data.get("location") or {}
    import_location(env, vals, location)

    if not vals.get("name"):
        vals["name"] = _generate_name(vals)

    return vals


def import_location(env, vals: dict[str, Any], location: dict[str, Any]) -> None:
    if not location:
        return

    city_name = location.get("city_name") or location.get("city")
    if city_name:
        city = env["estate.city"].search(
            [("name", "=", city_name)], limit=1
        )
        if city:
            vals["city_id"] = city.id
        else:
            _logger.warning("City '%s' not found, skipping", city_name)

    district_name = location.get("district_name") or location.get("district")
    if district_name:
        district = env["estate.district"].search(
            [("name", "=", district_name)], limit=1
        )
        if district:
            vals["district_id"] = district.id
        else:
            _logger.warning("District '%s' not found, skipping", district_name)

    street_name = location.get("street")
    if street_name and vals.get("city_id"):
        street = env["estate.street"].search(
            [("name", "=", street_name), ("city_id", "=", vals["city_id"])],
            limit=1,
        )
        if street:
            vals["street_id"] = street.id

    if location.get("house_number"):
        vals["house_number"] = location["house_number"]

    if location.get("residential_complex"):
        vals["residential_complex"] = location["residential_complex"]

    if location.get("apartment_number"):
        vals["apartment_number"] = location["apartment_number"]

    if location.get("latitude") is not None:
        vals["latitude"] = float(location["latitude"])

    if location.get("longitude") is not None:
        vals["longitude"] = float(location["longitude"])


def _generate_name(vals: dict[str, Any]) -> str:
    parts = []
    label = PROPERTY_TYPE_LABELS.get(vals.get("property_type"), "Объект")
    parts.append(label)

    if vals.get("area_total"):
        parts.append(f"{vals['area_total']} м²")

    if vals.get("price"):
        parts.append(f"{vals['price']:,.0f}")

    return " — ".join(parts) if len(parts) > 1 else parts[0]
