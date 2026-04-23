from dataclasses import dataclass


@dataclass(frozen=True)
class SnapshotCollectorConfig:
    min_sample_size: int = 20
    outlier_cut_percent: float = 0.05
    default_max_pages: int = 5
    inter_page_sleep_seconds: float = 3.0
    inter_target_sleep_seconds: float = 3.0


@dataclass(frozen=True)
class SnapshotTarget:
    config_id: int
    city_id: int
    city_name: str
    district_id: int | None
    district_name: str | None
    property_type: str
    rooms: int
    max_pages: int
