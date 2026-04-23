from .config import SnapshotTarget
from .protocols.i_price_stats_calculator import PriceStats


class SnapshotWriter:
    def __init__(self, env) -> None:
        self._env = env

    def write(self, target: SnapshotTarget, stats: PriceStats) -> int:
        record = self._env["estate.market.snapshot"].create({
            "city_id": target.city_id,
            "district_id": target.district_id or False,
            "property_type": target.property_type,
            "rooms": target.rooms,
            "sample_size": stats.sample_size,
            "median_price_per_sqm": stats.median_per_sqm,
            "p25_price_per_sqm": stats.p25_per_sqm,
            "p75_price_per_sqm": stats.p75_per_sqm,
            "currency": "KZT",
            "source": "krisha",
        })
        return record.id
