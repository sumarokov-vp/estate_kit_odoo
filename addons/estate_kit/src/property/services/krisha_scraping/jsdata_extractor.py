import json
import logging
import re
from typing import Any

from bs4 import BeautifulSoup

_logger = logging.getLogger(__name__)


class JsdataExtractor:
    _PATTERN = re.compile(r"window\.(?:__DATA__|data)\s*=\s*(\{.+\})")

    def extract(self, html: str) -> dict[str, Any] | None:
        soup = BeautifulSoup(html, "html.parser")
        script_tag = soup.find("script", {"id": "jsdata"})
        if not script_tag or not script_tag.string:
            return None
        match = self._PATTERN.search(script_tag.string)
        if not match:
            return None
        try:
            return json.loads(match.group(1))
        except (json.JSONDecodeError, KeyError) as exc:
            _logger.warning("Failed to parse jsdata: %s", exc)
            return None
