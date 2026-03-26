import logging
from typing import Any, Callable

from .protocols import IPropertyDataFetcher

_logger = logging.getLogger(__name__)

ApiDataImporter = Callable[[Any, dict[str, Any]], dict[str, Any]]


class NewListingHandler:
    def __init__(
        self,
        property_data_fetcher: IPropertyDataFetcher,
        import_from_api_data: ApiDataImporter,
        env: Any,
    ) -> None:
        self._property_data_fetcher = property_data_fetcher
        self._import_from_api_data = import_from_api_data
        self._env = env

    def handle(self, payload: dict[str, Any]) -> None:
        property_id = payload.get("data", {}).get("property_id")
        if not property_id:
            _logger.warning("mls.new_listing: missing property_id in payload")
            return

        existing = self._env["estate.property"].sudo().search(
            [("external_id", "=", property_id)], limit=1
        )
        if existing:
            _logger.info(
                "mls.new_listing: property with external_id=%d already exists", property_id
            )
            return

        item = self._property_data_fetcher.fetch(property_id)
        if not item:
            return

        vals = self._import_from_api_data(self._env, item)
        vals["external_id"] = property_id
        vals["state"] = "mls_listed"
        self._env["estate.property"].sudo().with_context(
            skip_api_sync=True, force_state_change=True
        ).create(vals)
        _logger.info("mls.new_listing: created property with external_id=%d", property_id)
