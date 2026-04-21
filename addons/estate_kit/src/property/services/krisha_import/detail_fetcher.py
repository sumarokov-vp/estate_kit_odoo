from typing import Any

from ..krisha_parser import KrishaParser


class DetailFetcher:
    def __init__(self, parser: KrishaParser) -> None:
        self._parser = parser

    def fetch(self, krisha_url: str) -> dict[str, Any]:
        return self._parser.fetch_property_details(krisha_url)
