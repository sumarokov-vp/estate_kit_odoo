import statistics

from .config import SnapshotCollectorConfig
from .protocols import IOutlierTrimmer, IPercentileCalculator
from .protocols.i_price_stats_calculator import PriceStats


class PriceStatsCalculator:
    def __init__(
        self,
        config: SnapshotCollectorConfig,
        outlier_trimmer: IOutlierTrimmer,
        percentile_calculator: IPercentileCalculator,
    ) -> None:
        self._config = config
        self._outlier_trimmer = outlier_trimmer
        self._percentile_calculator = percentile_calculator

    def calculate(self, samples: list[float]) -> PriceStats | None:
        if len(samples) < self._config.min_sample_size:
            return None

        trimmed = self._outlier_trimmer.trim(samples)
        if len(trimmed) < self._config.min_sample_size:
            return None

        sorted_samples = sorted(trimmed)
        return PriceStats(
            sample_size=len(sorted_samples),
            median_per_sqm=statistics.median(sorted_samples),
            p25_per_sqm=self._percentile_calculator.calculate(sorted_samples, 25),
            p75_per_sqm=self._percentile_calculator.calculate(sorted_samples, 75),
        )
