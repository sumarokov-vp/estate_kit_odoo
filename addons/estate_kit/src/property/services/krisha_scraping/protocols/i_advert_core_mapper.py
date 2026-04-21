from typing import Any, Protocol


class IAdvertCoreMapper(Protocol):
    def map(self, advert: dict[str, Any]) -> dict[str, Any]: ...
