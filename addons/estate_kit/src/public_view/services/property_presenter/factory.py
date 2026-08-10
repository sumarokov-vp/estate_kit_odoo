from ....property.services.address import Factory as AddressServiceFactory
from .address_formatter import AddressFormatter
from .price_formatter import PriceFormatter
from .service import PropertyPresenterService


class Factory:
    @staticmethod
    def create(env) -> PropertyPresenterService:
        return PropertyPresenterService(
            address_formatter=Factory.create_address_formatter(env),
            price_formatter=Factory.create_price_formatter(),
        )

    @staticmethod
    def create_address_formatter(env) -> AddressFormatter:
        return AddressFormatter(AddressServiceFactory.create(env))

    @staticmethod
    def create_price_formatter() -> PriceFormatter:
        return PriceFormatter()
