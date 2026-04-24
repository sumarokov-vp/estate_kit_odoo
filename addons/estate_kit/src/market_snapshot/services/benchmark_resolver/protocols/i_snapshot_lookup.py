from typing import Protocol


class ISnapshotLookup(Protocol):
    def find_latest(
        self,
        city_id: int,
        district_id: int | None,
        property_type: str,
        rooms: int | None,
        max_age_days: int,
    ): ...

    def find_recent_samples(
        self,
        city_id: int,
        district_id: int | None,
        property_type: str,
        rooms: int | None,
        max_age_days: int,
        limit: int,
    ) -> list[tuple[int, list[float]]]: ...

    def browse_snapshot(self, snapshot_id: int): ...
