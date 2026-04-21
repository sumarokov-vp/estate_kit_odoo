from typing import Any, Protocol


class IDetailAdvertMapper(Protocol):
    def map(self, advert: dict[str, Any]) -> dict[str, Any]: ...
