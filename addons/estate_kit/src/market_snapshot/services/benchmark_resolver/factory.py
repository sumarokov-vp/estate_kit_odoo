from .config import BenchmarkResolverConfig
from .service import BenchmarkResolverService
from .snapshot_lookup import SnapshotLookup


class Factory:
    @staticmethod
    def create(env) -> BenchmarkResolverService:
        config = BenchmarkResolverConfig()
        return BenchmarkResolverService(
            lookup=SnapshotLookup(env),
            config=config,
        )
