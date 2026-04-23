from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class MarketBenchmark:
    median_price_per_sqm: float
    p25_price_per_sqm: float
    p75_price_per_sqm: float
    sample_size: int
    snapshot_id: int
    collected_at: datetime
    city_name: str
    district_name: str | None
    property_type: str
    rooms: int
    relax_level: str  # "exact" | "no_rooms" | "city_only"
