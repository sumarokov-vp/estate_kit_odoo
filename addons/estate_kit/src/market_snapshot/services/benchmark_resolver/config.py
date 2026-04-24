from dataclasses import dataclass


@dataclass(frozen=True)
class BenchmarkResolverConfig:
    window_days: int = 30
    aggregation_snapshots_limit: int = 10
    min_aggregated_sample_size: int = 30
