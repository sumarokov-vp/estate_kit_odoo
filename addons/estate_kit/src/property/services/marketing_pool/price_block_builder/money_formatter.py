from .protocols import INumberFormatter


class MoneyFormatter:
    def __init__(self, number_formatter: INumberFormatter, currency: str = "KZT") -> None:
        self._number_formatter = number_formatter
        self._currency = currency

    def format(self, value: float) -> str:
        return "%s %s" % (self._number_formatter.format_integer(value), self._currency)
