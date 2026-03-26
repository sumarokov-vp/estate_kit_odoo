import logging

from .....src.shared.services.api_mapper.importer import API_DEAL_TYPE_MAP, API_PROPERTY_TYPE_MAP
from .protocols import IApiClient

_logger = logging.getLogger(__name__)

_PROPERTY_TYPE_TO_API_ID = {v: k for k, v in {
    1: "apartment", 2: "house", 3: "townhouse", 4: "commercial", 5: "land",
}.items()}
_DEAL_TYPE_TO_API_ID = {v: k for k, v in {
    1: "sale", 2: "rent_long", 3: "rent_daily",
}.items()}


class MlsPropertySearcher:
    def __init__(self, api_client: IApiClient) -> None:
        self._api_client = api_client

    def search_mls(self, criteria: dict, limit: int, offset: int) -> list:
        if not self._api_client.is_configured:
            return []

        params: dict = {"limit": limit, "offset": offset}
        if criteria.get("property_type"):
            api_id = _PROPERTY_TYPE_TO_API_ID.get(criteria["property_type"])
            if api_id:
                params["property_type_id"] = api_id
        if criteria.get("deal_type"):
            api_id = _DEAL_TYPE_TO_API_ID.get(criteria["deal_type"])
            if api_id:
                params["deal_type_id"] = api_id
        if criteria.get("city_id"):
            params["city_id"] = criteria["city_id"]
        if criteria.get("min_price"):
            params["min_price"] = criteria["min_price"]
        if criteria.get("max_price"):
            params["max_price"] = criteria["max_price"]

        try:
            data = self._api_client.get("/mls/properties", params=params)
        except Exception:
            _logger.warning("MLS API unavailable, returning empty MLS results", exc_info=True)
            return []

        if not data or not isinstance(data, dict):
            return []

        items = data.get("items", [])
        results = []
        for item in items:
            prop_type_obj = item.get("property_type") or {}
            deal_type_obj = item.get("deal_type") or {}
            city_obj = item.get("city") or {}
            district_obj = item.get("district") or {}

            results.append({
                "id": item.get("id", 0),
                "source": "mls",
                "mls_id": item.get("id", 0),
                "property_type": API_PROPERTY_TYPE_MAP.get(
                    int(prop_type_obj["id"]) if prop_type_obj.get("id") else 0, "",
                ),
                "deal_type": API_DEAL_TYPE_MAP.get(
                    int(deal_type_obj["id"]) if deal_type_obj.get("id") else 0, "",
                ),
                "city": city_obj.get("name", ""),
                "district": district_obj.get("name", ""),
                "address": "",
                "rooms": item.get("rooms") or 0,
                "area": item.get("area") or 0.0,
                "floor": item.get("floor") or 0,
                "total_floors": item.get("total_floors") or 0,
                "price": item.get("price") or 0.0,
                "description": "",
                "thumbnail_url": item.get("thumbnail_url") or "",
                "photo_urls": [],
                "created_at": item.get("created_at") or "",
            })

        return results
