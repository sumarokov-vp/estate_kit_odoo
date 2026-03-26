import logging
from typing import Any

from .protocols import IActivityCreator, IPropertyFinder

_logger = logging.getLogger(__name__)


class RejectedHandler:
    def __init__(
        self,
        property_finder: IPropertyFinder,
        activity_creator: IActivityCreator,
    ) -> None:
        self._property_finder = property_finder
        self._activity_creator = activity_creator

    def handle(self, payload: dict[str, Any]) -> None:
        property_id, existing = self._property_finder.find(payload, "property.rejected")
        if not property_id or not existing:
            return

        data = payload.get("data", {})
        reason = data.get("reason", "")

        vals = {"state": "rejected"}
        if reason:
            vals["mls_rejection_reason"] = reason

        existing.with_context(skip_api_sync=True, force_state_change=True).write(vals)

        note = f"Объект отклонён MLS: {reason}" if reason else "Объект отклонён MLS"
        self._activity_creator.create(existing, "Объект отклонён MLS", note)

        _logger.info(
            "property.rejected: property %s state → rejected, reason: %s",
            property_id,
            reason,
        )
