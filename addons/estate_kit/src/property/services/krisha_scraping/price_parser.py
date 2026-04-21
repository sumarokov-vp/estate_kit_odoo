import re


class PriceParser:
    _NON_DIGIT = re.compile(r"\D")

    def parse(self, text: str) -> int:
        digits = self._NON_DIGIT.sub("", text)
        return int(digits) if digits else 0
