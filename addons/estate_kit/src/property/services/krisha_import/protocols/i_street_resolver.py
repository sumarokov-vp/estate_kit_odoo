from typing import Protocol


class IStreetResolver(Protocol):
    def resolve(self, street_name: str | None, city_id: int | None) -> int | None: ...
