import logging
from typing import Any

from .protocols import IPropertyFinder
from .state_map import STRING_STATE_MAP

_logger = logging.getLogger(__name__)


class TransitionHandler:
    def __init__(self, property_finder: IPropertyFinder) -> None:
        self._property_finder = property_finder

    def handle(self, payload: dict[str, Any]) -> None:
        data = payload.get("data", {})
        status = data.get("status")
        property_id, existing = self._property_finder.find(payload, "property.transition")
        if not property_id:
            return

        new_state = STRING_STATE_MAP.get(status)
        if not new_state:
            _logger.warning(
                "property.transition: unknown status=%s for property %s",
                status,
                property_id,
            )
            return

        if not existing:
            return

        existing.with_context(skip_api_sync=True, force_state_change=True).write({"state": new_state})
        _logger.info("property.transition: property %s state → %s", property_id, new_state)
