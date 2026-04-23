from ....property.services.krisha_import.listing_fetcher import ListingFetcher
from ....property.services.krisha_import.page_url_builder import PageUrlBuilder
from ....property.services.krisha_scraping import (
    AdvertCoreMapper,
    AreaExtractor,
    HtmlFallbackParser,
    HttpFetcher,
    HttpSession,
    JsdataExtractor,
    ListingAdvertMapper,
    ListingPageParser,
    PriceParser,
    RoomsExtractor,
)
from .config import SnapshotCollectorConfig
from .krisha_search_url_builder import KrishaSearchUrlBuilder
from .krisha_snapshot_fetcher import KrishaSnapshotFetcher
from .outlier_trimmer import OutlierTrimmer
from .percentile_calculator import PercentileCalculator
from .price_stats_calculator import PriceStatsCalculator
from .service import SnapshotCollectorService
from .snapshot_config_loader import SnapshotConfigLoader
from .snapshot_logger import SnapshotLogger
from .snapshot_writer import SnapshotWriter
from .target_formatter import TargetFormatter
from .time_sleeper import TimeSleeper


class Factory:
    @staticmethod
    def create(env) -> SnapshotCollectorService:
        config = SnapshotCollectorConfig()

        http_session = HttpSession()
        http_fetcher = HttpFetcher(http_session)
        rooms_extractor = RoomsExtractor()
        area_extractor = AreaExtractor()
        price_parser = PriceParser()
        jsdata_extractor = JsdataExtractor()
        advert_core_mapper = AdvertCoreMapper(rooms_extractor, area_extractor)
        listing_advert_mapper = ListingAdvertMapper(advert_core_mapper)
        html_fallback_parser = HtmlFallbackParser(rooms_extractor, price_parser)
        listing_page_parser = ListingPageParser(
            jsdata_extractor,
            listing_advert_mapper,
            html_fallback_parser,
        )
        page_url_builder = PageUrlBuilder()
        listing_fetcher = ListingFetcher(
            http_fetcher, listing_page_parser, page_url_builder,
        )

        target_formatter = TargetFormatter()
        sleeper = TimeSleeper()
        return SnapshotCollectorService(
            config_loader=SnapshotConfigLoader(env, config),
            url_builder=KrishaSearchUrlBuilder(),
            fetcher=KrishaSnapshotFetcher(
                listing_fetcher,
                sleeper,
                config.inter_page_sleep_seconds,
            ),
            stats_calculator=PriceStatsCalculator(
                config,
                OutlierTrimmer(config.outlier_cut_percent),
                PercentileCalculator(),
            ),
            writer=SnapshotWriter(env),
            logger=SnapshotLogger(env, target_formatter),
            sleeper=sleeper,
            inter_target_sleep_seconds=config.inter_target_sleep_seconds,
        )
