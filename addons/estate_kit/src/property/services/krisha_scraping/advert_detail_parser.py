import logging
from typing import Any

from .protocols import IDetailAdvertMapper, IJsdataExtractor

_logger = logging.getLogger(__name__)


class AdvertDetailParser:
    def __init__(
        self,
        jsdata_extractor: IJsdataExtractor,
        advert_mapper: IDetailAdvertMapper,
    ) -> None:
        self._jsdata_extractor = jsdata_extractor
        self._advert_mapper = advert_mapper

    def parse(self, html: str) -> dict[str, Any]:
        data = self._jsdata_extractor.extract(html)
        if not data:
            _logger.warning("No jsdata script found or regex did not match")
            return {}

        advert = data.get("advert", {})
        result = self._advert_mapper.map(advert)
        _logger.info("Parsed details: %d photos found", len(result.get("photo_urls", [])))
        return result
