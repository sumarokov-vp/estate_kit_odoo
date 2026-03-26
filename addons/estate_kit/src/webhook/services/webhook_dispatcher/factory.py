from typing import Any

from ..webhook_handlers import Factory as WebhookHandlersFactory
from .event_cleaner import EventCleaner
from .handler_registry import HandlerRegistry
from .service import WebhookDispatcherService


class Factory:
    @staticmethod
    def create(env: Any) -> WebhookDispatcherService:
        handlers_service = WebhookHandlersFactory.create(env)
        handler_registry = HandlerRegistry(handlers_service)
        event_cleaner = EventCleaner(env)
        return WebhookDispatcherService(handler_registry, event_cleaner)
