from dataclasses import dataclass
from typing import Protocol

from .i_sample_aggregator import AggregatedStats


@dataclass(frozen=True)
class AggregatedResult:
    stats: AggregatedStats
    latest_snapshot_id: int


class IAggregatedResolver(Protocol):
    def resolve(
        self,
        city_id: int,
        district_id: int | None,
        property_type: str,
        rooms: int | None,
        max_age_days: int,
    ) -> AggregatedResult | None: ...
