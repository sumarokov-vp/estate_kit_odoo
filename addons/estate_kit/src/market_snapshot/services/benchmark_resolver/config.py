from dataclasses import dataclass


@dataclass(frozen=True)
class BenchmarkResolverConfig:
    window_days: int = 30
