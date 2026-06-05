from .address_formatter import AddressFormatter
from .card_builder import CardBuilder
from .image_url_resolver import ImageUrlResolver
from .main_image_resolver import MainImageResolver
from .page_url_resolver import PageUrlResolver
from .price_formatter import PriceFormatter
from .service import SimilarCardBuilderService
from .specs_formatter import SpecsFormatter


class Factory:
    @staticmethod
    def create(env) -> SimilarCardBuilderService:
        card_builder = CardBuilder(
            page_url_resolver=PageUrlResolver(env),
            image_url_resolver=ImageUrlResolver(env, MainImageResolver()),
            address_formatter=AddressFormatter(),
            price_formatter=PriceFormatter(),
            specs_formatter=SpecsFormatter(),
        )
        return SimilarCardBuilderService(card_builder)
