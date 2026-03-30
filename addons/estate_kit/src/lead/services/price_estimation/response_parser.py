import logging
import re

_logger = logging.getLogger(__name__)


class ResponseParser:
    def parse(self, response: str) -> float:
        cleaned = re.sub(r"[^\d.]", "", response.strip())
        if not cleaned:
            _logger.warning("AI price estimation: could not parse response: %s", response[:200])
            return 0.0
        try:
            return float(cleaned)
        except ValueError:
            _logger.warning("AI price estimation: invalid number in response: %s", response[:200])
            return 0.0
