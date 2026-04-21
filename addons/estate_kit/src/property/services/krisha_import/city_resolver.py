from typing import Any


class CityResolver:
    def __init__(self, env) -> None:
        self._env = env

    def resolve(self, city_name: Any) -> int | None:
        if not city_name or not isinstance(city_name, str):
            return None
        needle = city_name.strip()
        if not needle:
            return None
        city = self._env["estate.city"].search([("name", "=ilike", needle)], limit=1)
        if city:
            return city.id
        city = self._env["estate.city"].search([("code", "=ilike", needle)], limit=1)
        return city.id if city else None
