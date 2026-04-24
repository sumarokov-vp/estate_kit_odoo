from dataclasses import dataclass

from .config import DeviationBucket
from .hedonic_factor import HedonicFactor


@dataclass(frozen=True)
class PriceScoreResult:
    score: int
    deviation: float
    expected_per_sqm: float
    actual_per_sqm: float
    benchmark_snapshot_id: int
    hedonic_multiplier: float
    hedonic_factors_applied: list[HedonicFactor]
    bucket_applied: DeviationBucket
