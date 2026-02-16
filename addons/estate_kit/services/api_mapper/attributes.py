import json
import logging
from typing import Any

_logger = logging.getLogger(__name__)

ATTRIBUTE_FIELD_MAP: dict[str, tuple[str, str]] = {
    # Odoo field -> (API attribute name, value field)
    # Integers
    "rooms": ("rooms", "value_int"),
    "floor": ("floor", "value_int"),
    "floors_total": ("total_floors", "value_int"),
    "year_built": ("year_built", "value_int"),
    "entrance": ("entrance", "value_int"),
    "bedrooms": ("bedrooms", "value_int"),
    "bathroom_count": ("bathroom_count", "value_int"),
    "parking_count": ("parking_count", "value_int"),
    "electricity_power": ("electricity_power", "value_int"),
    # Decimals
    "area_kitchen": ("kitchen_area", "value_decimal"),
    "area_living": ("living_area", "value_decimal"),
    "ceiling_height": ("ceiling_height", "value_decimal"),
    "area_land": ("area_land", "value_decimal"),
    "area_commercial": ("area_commercial", "value_decimal"),
    "area_warehouse": ("area_warehouse", "value_decimal"),
    # Enums (value_text)
    "building_type": ("building_type", "value_text"),
    "condition": ("condition", "value_text"),
    "bathroom": ("bathroom", "value_text"),
    "balcony": ("balcony", "value_text"),
    "parking": ("parking", "value_text"),
    "furniture": ("furniture", "value_text"),
    "internet": ("internet", "value_text"),
    "heating": ("heating_type", "value_text"),
    "gas": ("gas", "value_text"),
    "water": ("water", "value_text"),
    "sewage": ("sewage", "value_text"),
    "electricity": ("electricity", "value_text"),
    "wall_material": ("wall_material", "value_text"),
    "foundation": ("foundation", "value_text"),
    "roof_type": ("roof_type", "value_text"),
    "window_type": ("window_type", "value_text"),
    "commercial_type": ("commercial_type", "value_text"),
    "road_access": ("road_access", "value_text"),
    "ownership_type": ("ownership_type", "value_text"),
    "land_category": ("land_category", "value_text"),
    "land_status": ("land_status", "value_text"),
    # Booleans
    "balcony_glazed": ("balcony_glazed", "value_bool"),
    "isolated_rooms": ("isolated_rooms", "value_bool"),
    "storage": ("storage", "value_bool"),
    "quiet_yard": ("quiet_yard", "value_bool"),
    "kitchen_studio": ("kitchen_studio", "value_bool"),
    "new_plumbing": ("new_plumbing", "value_bool"),
    "built_in_kitchen": ("built_in_kitchen", "value_bool"),
    "security_intercom": ("security_intercom", "value_bool"),
    "security_video": ("security_video", "value_bool"),
    "security_alarm": ("security_alarm", "value_bool"),
    "security_fire_alarm": ("security_fire_alarm", "value_bool"),
    "security_coded_lock": ("security_coded_lock", "value_bool"),
    "security_concierge": ("security_concierge", "value_bool"),
    "is_pledged": ("is_pledged", "value_bool"),
    "is_privatized": ("is_privatized", "value_bool"),
    "documents_ready": ("documents_ready", "value_bool"),
    "encumbrance": ("encumbrance", "value_bool"),
    "communications_nearby": ("communications_nearby", "value_bool"),
    "has_showcase": ("has_showcase", "value_bool"),
    "separate_entrance": ("separate_entrance", "value_bool"),
    # Inverted boolean
    "not_corner": ("is_corner", "value_bool"),
}

CACHE_PARAM_KEY = "estate_kit.api_attribute_ids_cache"


def get_api_attribute_ids(env: Any) -> dict[str, int]:
    config = env["ir.config_parameter"].sudo()
    cached = config.get_param(CACHE_PARAM_KEY)
    if cached:
        return json.loads(cached)

    from ..api_client import EstateKitApiClient

    client = EstateKitApiClient(env)
    if not client._is_configured:
        _logger.warning("API not configured, cannot load attribute IDs")
        return {}

    response = client.get("/properties/attributes")
    if not response:
        _logger.warning("Failed to load attributes from API")
        return {}

    attributes = response if isinstance(response, list) else response.get("data", [])
    result: dict[str, int] = {}
    for attr in attributes:
        name = attr.get("name")
        attr_id = attr.get("id")
        if name and attr_id:
            result[name] = attr_id

    config.set_param(CACHE_PARAM_KEY, json.dumps(result))
    _logger.info("Cached %d API attribute IDs", len(result))
    return result
