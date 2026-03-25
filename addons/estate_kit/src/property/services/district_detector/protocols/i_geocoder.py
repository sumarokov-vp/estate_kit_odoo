from typing import Any, Protocol


class IGeocoder(Protocol):
    @property
    def is_configured(self) -> bool: ...

    def geocode_address(self, address: str) -> tuple[float, float] | None: ...

    def find_or_create_district(self, env: Any, lat: float, lon: float, city_id: int) -> Any: ...
