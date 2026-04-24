from .aggregated_resolver import AggregatedResolver
from .config import BenchmarkResolverConfig
from .sample_aggregator import SampleAggregator
from .service import BenchmarkResolverService
from .snapshot_lookup import SnapshotLookup


class Factory:
    @staticmethod
    def create(env) -> BenchmarkResolverService:
        config = BenchmarkResolverConfig()
        lookup = SnapshotLookup(env)
        aggregator = SampleAggregator(
            min_sample_size=config.min_aggregated_sample_size,
        )
        aggregated_resolver = AggregatedResolver(
            lookup=lookup,
            aggregator=aggregator,
            snapshots_limit=config.aggregation_snapshots_limit,
        )
        return BenchmarkResolverService(
            lookup=lookup,
            aggregated_resolver=aggregated_resolver,
            config=config,
        )
