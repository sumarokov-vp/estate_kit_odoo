from typing import Any

_BUILDING_TYPE_BY_KEYWORD: dict[str, str] = {
    "монолит": "monolith",
    "кирпич": "brick",
    "панель": "panel",
    "каркас": "metal_frame",
    "деревян": "wood",
}


class BuildingTypeResolver:
    def resolve(self, raw: Any) -> str | None:
        if not raw or not isinstance(raw, str):
            return None
        lowered = raw.lower()
        for keyword, code in _BUILDING_TYPE_BY_KEYWORD.items():
            if keyword in lowered:
                return code
        return None
