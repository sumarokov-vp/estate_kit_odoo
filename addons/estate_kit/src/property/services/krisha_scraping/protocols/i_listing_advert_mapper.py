from typing import Any, Protocol


class IListingAdvertMapper(Protocol):
    def map(self, advert: dict[str, Any]) -> dict[str, Any]: ...
