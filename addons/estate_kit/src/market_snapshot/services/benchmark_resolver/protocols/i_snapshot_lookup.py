from typing import Protocol

from .i_snapshot_record import ISnapshotRecord


class ISnapshotLookup(Protocol):
    def find_latest(
        self,
        city_id: int,
        district_id: int | None,
        property_type: str,
        rooms: int | None,
        max_age_days: int,
    ) -> ISnapshotRecord | None: ...

    def find_recent_samples(
        self,
        city_id: int,
        district_id: int | None,
        property_type: str,
        rooms: int | None,
        max_age_days: int,
        limit: int,
    ) -> list[tuple[int, list[float]]]: ...

    def browse_snapshot(self, snapshot_id: int) -> ISnapshotRecord: ...
