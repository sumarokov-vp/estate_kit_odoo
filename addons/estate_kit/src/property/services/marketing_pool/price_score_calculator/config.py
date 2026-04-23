from dataclasses import dataclass, field


@dataclass(frozen=True)
class HedonicCoefficients:
    first_floor_penalty: float = 0.95
    last_floor_penalty: float = 0.97
    parking_bonus: float = 1.03
    year_built_penalty_per_decade: float = 0.02
    year_built_reference: int = 2015
    condition_multipliers: dict[str, float] = field(default_factory=lambda: {
        "no_repair": 0.90,
        "cosmetic": 0.97,
        "euro": 1.05,
        "designer": 1.10,
    })


@dataclass(frozen=True)
class DeviationBucket:
    upper_bound: float  # правая граница включительно
    score: int


_DEFAULT_BUCKETS: tuple[DeviationBucket, ...] = (
    DeviationBucket(upper_bound=-0.20, score=10),
    DeviationBucket(upper_bound=-0.10, score=9),
    DeviationBucket(upper_bound=-0.05, score=8),
    DeviationBucket(upper_bound=-0.02, score=7),
    DeviationBucket(upper_bound=0.02, score=6),
    DeviationBucket(upper_bound=0.05, score=5),
    DeviationBucket(upper_bound=0.10, score=4),
    DeviationBucket(upper_bound=0.20, score=3),
    DeviationBucket(upper_bound=0.50, score=2),
    DeviationBucket(upper_bound=float("inf"), score=1),
)


@dataclass(frozen=True)
class PriceScoreConfig:
    hedonic: HedonicCoefficients = field(default_factory=HedonicCoefficients)
    deviation_buckets: tuple[DeviationBucket, ...] = _DEFAULT_BUCKETS
