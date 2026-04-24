from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class AggregatedStats:
    sample_size: int
    median_price_per_sqm: float
    p25_price_per_sqm: float
    p75_price_per_sqm: float


class ISampleAggregator(Protocol):
    def aggregate(self, samples_groups: list[list[float]]) -> AggregatedStats | None: ...
