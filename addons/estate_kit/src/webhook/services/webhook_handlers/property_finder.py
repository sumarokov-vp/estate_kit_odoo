import logging
from typing import Any

_logger = logging.getLogger(__name__)


class PropertyFinder:
    def __init__(self, env: Any) -> None:
        self._env = env

    def find(self, payload: dict[str, Any], event_name: str) -> tuple[int | None, Any]:
        property_id = payload.get("data", {}).get("property_id")
        if not property_id:
            _logger.warning("%s: missing property_id in payload", event_name)
            return None, None
        existing = self._env["estate.property"].sudo().search(
            [("external_id", "=", property_id)], limit=1
        )
        if not existing:
            _logger.warning(
                "%s: property with external_id=%s not found", event_name, property_id
            )
        return property_id, existing
