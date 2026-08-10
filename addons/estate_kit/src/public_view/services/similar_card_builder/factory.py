from ..property_presenter import Factory as PropertyPresenterFactory
from .card_builder import CardBuilder
from .image_url_resolver import ImageUrlResolver
from .main_image_resolver import MainImageResolver
from .page_url_resolver import PageUrlResolver
from .service import SimilarCardBuilderService
from .specs_formatter import SpecsFormatter


class Factory:
    @staticmethod
    def create(env) -> SimilarCardBuilderService:
        card_builder = CardBuilder(
            page_url_resolver=PageUrlResolver(env),
            image_url_resolver=ImageUrlResolver(env, MainImageResolver()),
            address_formatter=PropertyPresenterFactory.create_address_formatter(env),
            price_formatter=PropertyPresenterFactory.create_price_formatter(),
            specs_formatter=SpecsFormatter(),
        )
        return SimilarCardBuilderService(card_builder)
