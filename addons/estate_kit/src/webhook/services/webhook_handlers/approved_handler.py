import logging
from typing import Any

from .protocols import IPropertyFinder

_logger = logging.getLogger(__name__)


class ApprovedHandler:
    def __init__(self, property_finder: IPropertyFinder) -> None:
        self._property_finder = property_finder

    def handle(self, payload: dict[str, Any]) -> None:
        property_id, existing = self._property_finder.find(payload, "property.approved")
        if not property_id or not existing:
            return

        existing.with_context(skip_api_sync=True, force_state_change=True).write({"state": "published"})
        _logger.info("property.approved: property %s state → published", property_id)
