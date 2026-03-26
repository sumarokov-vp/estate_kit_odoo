import logging
from typing import Any

from .protocols import IEventCleaner, IHandlerRegistry

_logger = logging.getLogger(__name__)


class WebhookDispatcherService:
    def __init__(
        self,
        handler_registry: IHandlerRegistry,
        event_cleaner: IEventCleaner,
    ) -> None:
        self._handler_registry = handler_registry
        self._event_cleaner = event_cleaner

    def dispatch(self, event_type: str, payload: dict[str, Any]) -> None:
        _logger.info("Webhook event received: %s", event_type)
        handler = self._handler_registry.get_handler(event_type)
        if handler is not None:
            handler(payload)

    def cleanup_old_events(self, retention_days: int) -> None:
        self._event_cleaner.cleanup(retention_days)
