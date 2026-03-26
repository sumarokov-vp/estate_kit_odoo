from typing import Any, Callable, Protocol


class IWebhookHandlers(Protocol):
    def handle_transition(self, payload: dict[str, Any]) -> None: ...
    def handle_approved(self, payload: dict[str, Any]) -> None: ...
    def handle_rejected(self, payload: dict[str, Any]) -> None: ...
    def handle_delisted(self, payload: dict[str, Any]) -> None: ...
    def handle_contact_request(self, payload: dict[str, Any]) -> None: ...
    def handle_new_listing(self, payload: dict[str, Any]) -> None: ...
    def handle_listing_removed(self, payload: dict[str, Any]) -> None: ...


class HandlerRegistry:
    def __init__(self, handlers: IWebhookHandlers) -> None:
        self._registry: dict[str, Callable[[dict[str, Any]], None]] = {
            "property.created": handlers.handle_transition,
            "property.approved": handlers.handle_approved,
            "property.rejected": handlers.handle_rejected,
            "property.delisted": handlers.handle_delisted,
            "contact.requested": handlers.handle_contact_request,
            "mls.new_listing": handlers.handle_new_listing,
            "mls.listing_removed": handlers.handle_listing_removed,
        }

    def get_handler(self, event_type: str) -> Callable[[dict[str, Any]], None] | None:
        return self._registry.get(event_type)
