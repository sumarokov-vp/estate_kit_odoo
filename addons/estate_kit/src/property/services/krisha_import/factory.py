from ..krisha_parser import KrishaParser
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
        parser = KrishaParser()
        config_provider = ConfigProvider(env)
        listing_fetcher = ListingFetcher(parser)
        detail_fetcher = DetailFetcher(parser)
        duplicate_checker = DuplicateChecker(env)
        city_resolver = CityResolver(env)
        building_type_resolver = BuildingTypeResolver()
        field_mapper = FieldMapper(city_resolver, building_type_resolver)
        property_creator = PropertyCreator(env, field_mapper)
        photo_importer = PhotoImporter(env, parser)
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
