from datetime import datetime
from typing import Protocol


class ICityRecord(Protocol):
    name: str


class IDistrictRecord(Protocol):
    name: str


class ISnapshotRecord(Protocol):
    id: int
    collected_at: datetime
    city_id: ICityRecord
    district_id: IDistrictRecord | None
    property_type: str
    rooms: int
    sample_size: int
    median_price_per_sqm: float
    p25_price_per_sqm: float
    p75_price_per_sqm: float
