from .protocols import IAddressFormatter, IPriceFormatter


class PropertyPresenterService:
    def __init__(
        self,
        address_formatter: IAddressFormatter,
        price_formatter: IPriceFormatter,
    ) -> None:
        self._address_formatter = address_formatter
        self._price_formatter = price_formatter

    def address(self, prop) -> str:
        return self._address_formatter.format(prop)

    def price_text(self, prop) -> str:
        return self._price_formatter.format(prop)
