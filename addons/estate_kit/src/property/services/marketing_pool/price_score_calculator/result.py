from dataclasses import dataclass


@dataclass(frozen=True)
class PriceScoreResult:
    score: int
    deviation: float
    expected_per_sqm: float
    actual_per_sqm: float
    benchmark_snapshot_id: int
    hedonic_multiplier: float
    hedonic_factors_applied: list[str]
