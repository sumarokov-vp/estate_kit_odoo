class LocalPropertySearcher:
    def __init__(self, env) -> None:
        self._env = env

    def search_local(self, criteria: dict, limit: int, offset: int) -> list:
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
