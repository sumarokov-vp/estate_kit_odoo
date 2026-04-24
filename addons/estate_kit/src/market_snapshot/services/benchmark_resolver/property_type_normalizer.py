_ALIAS_MAP: dict[str, str] = {
    "townhouse": "house",
}


class PropertyTypeNormalizer:
    def normalize(self, property_type: str) -> str:
        return _ALIAS_MAP.get(property_type, property_type)
