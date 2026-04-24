from .protocols import ISampleAggregator, ISnapshotLookup
from .protocols.i_aggregated_resolver import AggregatedResult


class AggregatedResolver:
    def __init__(
        self,
        lookup: ISnapshotLookup,
        aggregator: ISampleAggregator,
        snapshots_limit: int,
    ) -> None:
        self._lookup = lookup
        self._aggregator = aggregator
        self._snapshots_limit = snapshots_limit

    def resolve(
        self,
        city_id: int,
        district_id: int | None,
        property_type: str,
        rooms: int | None,
        max_age_days: int,
    ) -> AggregatedResult | None:
        groups = self._lookup.find_recent_samples(
            city_id=city_id,
            district_id=district_id,
            property_type=property_type,
            rooms=rooms,
            max_age_days=max_age_days,
            limit=self._snapshots_limit,
        )
        if not groups:
            return None
        stats = self._aggregator.aggregate([samples for _, samples in groups])
        if stats is None:
            return None
        return AggregatedResult(stats=stats, latest_snapshot_id=groups[0][0])
