_NBSP = " "
_MINUS = "−"


class NumberFormatter:
    def format_integer(self, value: float) -> str:
        rounded = int(round(value))
        negative = rounded < 0
        digits = str(abs(rounded))
        groups: list[str] = []
        while len(digits) > 3:
            groups.insert(0, digits[-3:])
            digits = digits[:-3]
        groups.insert(0, digits)
        formatted = _NBSP.join(groups)
        if negative:
            return _MINUS + formatted
        return formatted

    def format_percent_signed(self, value: float) -> str:
        sign = "+" if value >= 0 else _MINUS
        return "%s%.1f%%" % (sign, abs(value))
