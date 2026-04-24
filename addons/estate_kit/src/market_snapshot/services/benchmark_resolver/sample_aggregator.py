import statistics
from dataclasses import dataclass


@dataclass(frozen=True)
class AggregatedStats:
    sample_size: int
    median_price_per_sqm: float
    p25_price_per_sqm: float
    p75_price_per_sqm: float


class SampleAggregator:
    def __init__(self, min_sample_size: int) -> None:
        self._min_sample_size = min_sample_size

    def aggregate(self, samples_groups: list[list[float]]) -> AggregatedStats | None:
        merged: list[float] = []
        for group in samples_groups:
            merged.extend(group)
        if len(merged) < self._min_sample_size:
            return None

        merged.sort()
        return AggregatedStats(
            sample_size=len(merged),
            median_price_per_sqm=statistics.median(merged),
            p25_price_per_sqm=_percentile(merged, 25),
            p75_price_per_sqm=_percentile(merged, 75),
        )


def _percentile(sorted_values: list[float], percentile: int) -> float:
    if not sorted_values:
        return 0.0
    n = len(sorted_values)
    rank = (percentile / 100) * (n - 1)
    lower = int(rank)
    upper = min(lower + 1, n - 1)
    weight = rank - lower
    return sorted_values[lower] * (1 - weight) + sorted_values[upper] * weight
