from .protocols import (
    IAddressFormatter,
    IImageUrlResolver,
    IPageUrlResolver,
    IPriceFormatter,
    ISpecsFormatter,
)


class CardBuilder:
    def __init__(
        self,
        page_url_resolver: IPageUrlResolver,
        image_url_resolver: IImageUrlResolver,
        address_formatter: IAddressFormatter,
        price_formatter: IPriceFormatter,
        specs_formatter: ISpecsFormatter,
    ) -> None:
        self._page_url_resolver = page_url_resolver
        self._image_url_resolver = image_url_resolver
        self._address_formatter = address_formatter
        self._price_formatter = price_formatter
        self._specs_formatter = specs_formatter

    def build(self, prop) -> dict:
        return {
            "url": self._page_url_resolver.resolve(prop),
            "image_url": self._image_url_resolver.resolve(prop),
            "title": prop.name,
            "address": self._address_formatter.format(prop),
            "price": self._price_formatter.format(prop),
            "specs": self._specs_formatter.format(prop),
        }
