from dataclasses import dataclass


@dataclass(frozen=True)
class ScoringConfig:
    same_district_weight: float = 30.0
    price_weight: float = 40.0
    price_tolerance: float = 0.25
    area_weight: float = 20.0
    area_tolerance: float = 0.20
    rooms_weight: float = 10.0
    rooms_tolerance: int = 1


ACTIVE_STATES = ("active", "published", "mls_listed")

RESIDENTIAL_TYPES = ("apartment", "house", "townhouse")

DEFAULT_CONFIG = ScoringConfig()
