import logging
from typing import Any

from bs4 import BeautifulSoup

from .protocols import (
    IAdvertInfoHtmlExtractor,
    IDetailAdvertMapper,
    IJsdataExtractor,
    IResidentialComplexHtmlExtractor,
)

_logger = logging.getLogger(__name__)


class AdvertDetailParser:
    def __init__(
        self,
        jsdata_extractor: IJsdataExtractor,
        advert_mapper: IDetailAdvertMapper,
        residential_complex_extractor: IResidentialComplexHtmlExtractor,
        info_extractor: IAdvertInfoHtmlExtractor,
    ) -> None:
        self._jsdata_extractor = jsdata_extractor
        self._advert_mapper = advert_mapper
        self._residential_complex_extractor = residential_complex_extractor
        self._info_extractor = info_extractor

    def parse(self, html: str) -> dict[str, Any]:
        data = self._jsdata_extractor.extract(html)
        if not data:
            _logger.warning("No jsdata script found or regex did not match")
            return {}

        advert = data.get("advert", {})
        result = self._advert_mapper.map(advert)

        soup = BeautifulSoup(html, "html.parser")
        complex_info = self._residential_complex_extractor.extract(soup)
        if complex_info.get("name"):
            result["residential_complex_name"] = complex_info["name"]
        if complex_info.get("krisha_url"):
            result["residential_complex_krisha_url"] = complex_info["krisha_url"]

        info = self._info_extractor.extract(soup)
        for key, value in info.items():
            if value in (None, ""):
                continue
            if not result.get(key):
                result[key] = value

        return result
