import logging
from typing import Any

from .protocols import IApiClient

_logger = logging.getLogger(__name__)


class PropertyDataFetcher:
    def __init__(self, api_client: IApiClient) -> None:
        self._api_client = api_client

    def fetch(self, property_id: int) -> dict[str, Any] | None:
        item = self._api_client.get(f"/mls/properties/{property_id}")
        if not item:
            _logger.warning(
                "mls.new_listing: failed to fetch property %d from API", property_id
            )
        return item
