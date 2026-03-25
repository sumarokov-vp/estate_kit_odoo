import logging

from .protocols import IApiClient

_logger = logging.getLogger(__name__)

_PROPERTY_TYPE_TO_API_ID = {v: k for k, v in {
    1: "apartment", 2: "house", 3: "townhouse", 4: "commercial", 5: "land",
}.items()}
_DEAL_TYPE_TO_API_ID = {v: k for k, v in {
    1: "sale", 2: "rent_long", 3: "rent_daily",
}.items()}


class UnifiedSearchService:
    def __init__(self, api_client: IApiClient, env) -> None:
        self._api_client = api_client
        self._env = env

    def search_unified(self, criteria: dict, limit: int = 50, offset: int = 0, count: bool = False) -> list | int:
        criteria = criteria or {}
        local_results = self._search_local(criteria, limit, offset)
        mls_results = self._search_mls(criteria, limit, offset)

        local_mls_ids = {r["mls_id"] for r in local_results if r.get("mls_id")}
        merged = list(local_results)
        for item in mls_results:
            if item.get("mls_id") and item["mls_id"] not in local_mls_ids:
                merged.append(item)

        if count:
            return len(merged)

        return merged[:limit]

    def _search_local(self, criteria: dict, limit: int, offset: int) -> list:
        domain = [("active", "=", True)]

        if criteria.get("deal_type"):
            domain.append(("deal_type", "=", criteria["deal_type"]))
        if criteria.get("property_type"):
            domain.append(("property_type", "=", criteria["property_type"]))
        if criteria.get("city_id"):
            domain.append(("city_id", "=", criteria["city_id"]))
        if criteria.get("district_id"):
            domain.append(("district_id", "=", criteria["district_id"]))
        if criteria.get("rooms"):
            domain.append(("rooms", "=", criteria["rooms"]))
        if criteria.get("min_price"):
            domain.append(("price", ">=", criteria["min_price"]))
        if criteria.get("max_price"):
            domain.append(("price", "<=", criteria["max_price"]))
        if criteria.get("min_area"):
            domain.append(("area_total", ">=", criteria["min_area"]))
        if criteria.get("max_area"):
            domain.append(("area_total", "<=", criteria["max_area"]))
        if criteria.get("floor_min"):
            domain.append(("floor", ">=", criteria["floor_min"]))
        if criteria.get("floor_max"):
            domain.append(("floor", "<=", criteria["floor_max"]))

        records = self._env["estate.property"].search_read(
            domain,
            fields=[
                "id", "external_id", "property_type", "deal_type",
                "city_id", "district_id", "street_id", "house_number",
                "rooms", "area_total", "floor", "floors_total",
                "price", "description", "create_date",
            ],
            limit=limit,
            offset=offset,
            order="create_date desc",
        )

        results = []
        for rec in records:
            city_name = rec["city_id"][1] if rec.get("city_id") else ""
            district_name = rec["district_id"][1] if rec.get("district_id") else ""
            street_name = rec["street_id"][1] if rec.get("street_id") else ""
            address_parts = [p for p in [city_name, district_name, street_name, rec.get("house_number") or ""] if p]

            photo_urls = []
            thumbnail_url = ""
            images = self._env["estate.property.image"].search_read(
                [("property_id", "=", rec["id"])],
                fields=["image_url"],
                limit=10,
            )
            for img in images:
                if img.get("image_url"):
                    photo_urls.append(img["image_url"])
            if photo_urls:
                thumbnail_url = photo_urls[0]

            results.append({
                "id": rec["id"],
                "source": "local",
                "mls_id": rec.get("external_id") or 0,
                "property_type": rec.get("property_type") or "",
                "deal_type": rec.get("deal_type") or "",
                "city": city_name,
                "district": district_name,
                "address": ", ".join(address_parts),
                "rooms": rec.get("rooms") or 0,
                "area": rec.get("area_total") or 0.0,
                "floor": rec.get("floor") or 0,
                "total_floors": rec.get("floors_total") or 0,
                "price": rec.get("price") or 0.0,
                "description": rec.get("description") or "",
                "thumbnail_url": thumbnail_url,
                "photo_urls": photo_urls,
                "created_at": rec.get("create_date") or "",
            })

        return results

    def _search_mls(self, criteria: dict, limit: int, offset: int) -> list:
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

        from .....services.api_mapper.importer import API_DEAL_TYPE_MAP, API_PROPERTY_TYPE_MAP

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
