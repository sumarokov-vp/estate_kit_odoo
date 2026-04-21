import re


class RoomsExtractor:
    _PATTERN = re.compile(r"(\d+)-комн")

    def extract(self, title: str) -> int:
        match = self._PATTERN.search(title)
        if match:
            return int(match.group(1))
        return 0
