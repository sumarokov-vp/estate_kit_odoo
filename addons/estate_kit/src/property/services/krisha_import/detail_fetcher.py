import logging
from typing import Any

from ..krisha_scraping.protocols import IAdvertDetailParser, IHttpFetcher

_logger = logging.getLogger(__name__)


class DetailFetcher:
    def __init__(
        self,
        http_fetcher: IHttpFetcher,
        detail_parser: IAdvertDetailParser,
    ) -> None:
        self._http_fetcher = http_fetcher
        self._detail_parser = detail_parser

    def fetch(self, krisha_url: str) -> dict[str, Any]:
        _logger.info("Fetching details from: %s", krisha_url)
        html = self._http_fetcher.fetch(krisha_url)
        return self._detail_parser.parse(html)
