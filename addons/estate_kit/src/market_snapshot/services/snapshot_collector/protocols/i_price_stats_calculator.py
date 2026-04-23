from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class PriceStats:
    sample_size: int
    median_per_sqm: float
    p25_per_sqm: float
    p75_per_sqm: float


class IPriceStatsCalculator(Protocol):
    def calculate(self, samples: list[float]) -> PriceStats | None: ...
