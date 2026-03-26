from typing import Any

from .protocols import (
    IApprovedHandler,
    IContactRequestHandler,
    IDelistedHandler,
    IListingRemovedHandler,
    INewListingHandler,
    IRejectedHandler,
    ITransitionHandler,
)


class WebhookHandlersService:
    def __init__(
        self,
        transition_handler: ITransitionHandler,
        approved_handler: IApprovedHandler,
        rejected_handler: IRejectedHandler,
        delisted_handler: IDelistedHandler,
        contact_request_handler: IContactRequestHandler,
        new_listing_handler: INewListingHandler,
        listing_removed_handler: IListingRemovedHandler,
    ) -> None:
        self._transition_handler = transition_handler
        self._approved_handler = approved_handler
        self._rejected_handler = rejected_handler
        self._delisted_handler = delisted_handler
        self._contact_request_handler = contact_request_handler
        self._new_listing_handler = new_listing_handler
        self._listing_removed_handler = listing_removed_handler

    def handle_transition(self, payload: dict[str, Any]) -> None:
        self._transition_handler.handle(payload)

    def handle_approved(self, payload: dict[str, Any]) -> None:
        self._approved_handler.handle(payload)

    def handle_rejected(self, payload: dict[str, Any]) -> None:
        self._rejected_handler.handle(payload)

    def handle_delisted(self, payload: dict[str, Any]) -> None:
        self._delisted_handler.handle(payload)

    def handle_contact_request(self, payload: dict[str, Any]) -> None:
        self._contact_request_handler.handle(payload)

    def handle_new_listing(self, payload: dict[str, Any]) -> None:
        self._new_listing_handler.handle(payload)

    def handle_listing_removed(self, payload: dict[str, Any]) -> None:
        self._listing_removed_handler.handle(payload)
