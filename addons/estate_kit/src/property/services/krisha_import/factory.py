from ..krisha_scraping import (
    AdvertCoreMapper,
    AdvertDetailParser,
    AreaExtractor,
    DetailAdvertMapper,
    HtmlFallbackParser,
    HttpFetcher,
    HttpSession,
    ImageDownloader,
    JsdataExtractor,
    ListingAdvertMapper,
    ListingPageParser,
    PriceParser,
    RoomsExtractor,
)
from .building_type_resolver import BuildingTypeResolver
from .city_resolver import CityResolver
from .config_provider import ConfigProvider
from .detail_fetcher import DetailFetcher
from .duplicate_checker import DuplicateChecker
from .field_mapper import FieldMapper
from .import_logger import ImportLogger
from .listing_fetcher import ListingFetcher
from .photo_importer import PhotoImporter
from .property_creator import PropertyCreator
from .service import KrishaImportService


class Factory:
    @staticmethod
    def create(env) -> KrishaImportService:
        http_session = HttpSession()
        http_fetcher = HttpFetcher(http_session)
        image_downloader = ImageDownloader(http_session)

        rooms_extractor = RoomsExtractor()
        area_extractor = AreaExtractor()
        price_parser = PriceParser()
        jsdata_extractor = JsdataExtractor()
        advert_core_mapper = AdvertCoreMapper(rooms_extractor, area_extractor)
        listing_advert_mapper = ListingAdvertMapper(advert_core_mapper)
        detail_advert_mapper = DetailAdvertMapper(advert_core_mapper)
        html_fallback_parser = HtmlFallbackParser(rooms_extractor, price_parser)
        listing_page_parser = ListingPageParser(
            jsdata_extractor,
            listing_advert_mapper,
            html_fallback_parser,
        )
        advert_detail_parser = AdvertDetailParser(jsdata_extractor, detail_advert_mapper)

        config_provider = ConfigProvider(env)
        listing_fetcher = ListingFetcher(http_fetcher, listing_page_parser)
        detail_fetcher = DetailFetcher(http_fetcher, advert_detail_parser)
        duplicate_checker = DuplicateChecker(env)
        city_resolver = CityResolver(env)
        building_type_resolver = BuildingTypeResolver()
        field_mapper = FieldMapper(city_resolver, building_type_resolver)
        property_creator = PropertyCreator(env, field_mapper)
        photo_importer = PhotoImporter(env, image_downloader)
        logger = ImportLogger(env)
        return KrishaImportService(
            config_provider,
            listing_fetcher,
            detail_fetcher,
            duplicate_checker,
            property_creator,
            photo_importer,
            logger,
        )
