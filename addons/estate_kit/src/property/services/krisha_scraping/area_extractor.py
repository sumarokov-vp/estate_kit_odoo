import re
from typing import Any


class AreaExtractor:
    _PATTERN = re.compile(r"(\d+(?:\.\d+)?)")

    def extract(self, value: Any) -> float:
        if isinstance(value, (int, float)):
            return float(value)
        if isinstance(value, str):
            match = self._PATTERN.search(value)
            if match:
                return float(match.group(1))
        return 0.0
