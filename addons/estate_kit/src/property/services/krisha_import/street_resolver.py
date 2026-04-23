import logging

_logger = logging.getLogger(__name__)


class StreetResolver:
    def __init__(self, env) -> None:
        self._env = env

    def resolve(self, street_name: str | None, city_id: int | None) -> int | None:
        if not street_name or not isinstance(street_name, str):
            return None
        needle = street_name.strip()
        if not needle or not city_id:
            return None

        model = self._env["estate.street"]
        record = model.search(
            [("name", "=ilike", needle), ("city_id", "=", city_id)],
            limit=1,
        )
        if record:
            return record.id

        record = model.create({"name": needle, "city_id": city_id})
        _logger.info("Created street %s (city_id=%s)", needle, city_id)
        return record.id
