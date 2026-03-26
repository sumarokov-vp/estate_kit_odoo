from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class PoolScoreConfig:
    w_scoring: float
    w_tier: float
    t_include: float
    t_exclude: float
    min_price: int
    min_quality: int
    min_listing: int

    @classmethod
    def from_env(cls, env: Any) -> "PoolScoreConfig":
        get_param = env["ir.config_parameter"].sudo().get_param
        return cls(
            w_scoring=float(get_param("estate_kit.pool_scoring_weight", "0.6")),
            w_tier=float(get_param("estate_kit.pool_tier_weight", "0.4")),
            t_include=float(get_param("estate_kit.pool_inclusion_threshold", "7.0")),
            t_exclude=float(get_param("estate_kit.pool_exclusion_threshold", "4.0")),
            min_price=int(get_param("estate_kit.pool_min_price_score", "3")),
            min_quality=int(get_param("estate_kit.pool_min_quality_score", "3")),
            min_listing=int(get_param("estate_kit.pool_min_listing_score", "3")),
        )
