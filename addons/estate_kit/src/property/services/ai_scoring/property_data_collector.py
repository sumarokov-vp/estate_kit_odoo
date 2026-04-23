from .protocols import IPropertyValueTransformer


class PropertyDataCollector:
    def __init__(self, value_transformer: IPropertyValueTransformer) -> None:
        self._value_transformer = value_transformer

    def collect(self, prop, benchmark=None) -> dict:
        get = self._value_transformer.get_value
        price_per_sqm = 0
        if prop.price and prop.area_total:
            price_per_sqm = round(prop.price / prop.area_total)

        data = {
            "property_type": get(prop, "property_type"),
            "deal_type": get(prop, "deal_type"),
            "price": prop.price,
            "price_per_sqm": price_per_sqm,
            "currency": prop.currency_id.name if prop.currency_id else "",
            "area_total": prop.area_total,
            "city": prop.city_id.name if prop.city_id else "",
            "district": prop.district_id.name if prop.district_id else "",
            "description": (prop.description or "")[:1000],
            "photo_count": len(prop.image_ids),
            "rooms": get(prop, "rooms"),
            "bedrooms": get(prop, "bedrooms"),
            "floor": get(prop, "floor"),
            "floors_total": get(prop, "floors_total"),
            "year_built": get(prop, "year_built"),
            "building_type": get(prop, "building_type"),
            "ceiling_height": get(prop, "ceiling_height"),
            "condition": get(prop, "condition"),
            "area_living": get(prop, "area_living"),
            "area_kitchen": get(prop, "area_kitchen"),
            "area_land": get(prop, "area_land"),
            "area_commercial": get(prop, "area_commercial"),
            "area_warehouse": get(prop, "area_warehouse"),
            "wall_material": get(prop, "wall_material"),
            "roof_type": get(prop, "roof_type"),
            "foundation": get(prop, "foundation"),
            "bathroom": get(prop, "bathroom"),
            "balcony": get(prop, "balcony"),
            "parking": get(prop, "parking"),
            "furniture": get(prop, "furniture"),
            "heating": get(prop, "heating"),
            "water": get(prop, "water"),
            "sewage": get(prop, "sewage"),
            "gas": get(prop, "gas"),
            "electricity": get(prop, "electricity"),
            "internet": get(prop, "internet"),
            "residential_complex": prop.residential_complex_id.name or "" if prop.residential_complex_id else "",
            "commercial_type": get(prop, "commercial_type"),
            "separate_entrance": get(prop, "separate_entrance"),
            "has_showcase": get(prop, "has_showcase"),
            "electricity_power": get(prop, "electricity_power"),
            "communications_nearby": get(prop, "communications_nearby"),
            "land_category": get(prop, "land_category"),
            "land_status": get(prop, "land_status"),
            "road_access": get(prop, "road_access"),
        }
        if benchmark is not None:
            data["market_benchmark"] = {
                "median_per_sqm": benchmark.median_price_per_sqm,
                "p25_per_sqm": benchmark.p25_price_per_sqm,
                "p75_per_sqm": benchmark.p75_price_per_sqm,
                "sample_size": benchmark.sample_size,
                "collected_at": benchmark.collected_at.strftime("%d.%m.%Y"),
                "relax_level": benchmark.relax_level,
                "city": benchmark.city_name,
                "district": benchmark.district_name or "",
                "rooms": benchmark.rooms,
            }
        return data
