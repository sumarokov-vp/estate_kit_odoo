from dataclasses import dataclass, field


@dataclass(frozen=True)
class SearchCriteria:
    deal_type: str | None = None
    property_type: str | None = None
    city: str | None = None
    districts: list[str] = field(default_factory=list)
    rooms_min: int | None = None
    rooms_max: int | None = None
    price_min: float | None = None
    price_max: float | None = None
    area_min: float | None = None
    area_max: float | None = None
