import logging
from typing import Any

from .protocols import IActivityCreator, IPropertyFinder

_logger = logging.getLogger(__name__)


class ContactRequestHandler:
    def __init__(
        self,
        property_finder: IPropertyFinder,
        activity_creator: IActivityCreator,
    ) -> None:
        self._property_finder = property_finder
        self._activity_creator = activity_creator

    def handle(self, payload: dict[str, Any]) -> None:
        property_id, prop = self._property_finder.find(payload, "contact.requested")
        if not property_id or not prop:
            return

        responsible_user = prop.user_id or prop.listing_agent_id
        if not responsible_user:
            _logger.warning(
                "contact.requested: no responsible user for property id=%s",
                prop.id,
            )
            return

        data = payload.get("data", {})
        requester_tenant_id = data.get("requester_tenant_id")
        note = "Запрос контакта собственника"
        if requester_tenant_id:
            note += f" (tenant_id: {requester_tenant_id})"

        self._activity_creator.create(prop, "Запрос контакта собственника", note)

        _logger.info(
            "contact.requested: created activity for property id=%s, user=%s",
            prop.id,
            responsible_user.login,
        )
