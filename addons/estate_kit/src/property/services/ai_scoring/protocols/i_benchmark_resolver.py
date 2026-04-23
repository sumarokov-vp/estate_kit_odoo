from typing import Protocol

from .....market_snapshot.services.benchmark_resolver import MarketBenchmark


class IBenchmarkResolver(Protocol):
    def resolve(self, prop) -> MarketBenchmark | None: ...
