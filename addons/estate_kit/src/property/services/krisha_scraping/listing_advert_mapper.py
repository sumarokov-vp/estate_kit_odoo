from typing import Any

from .protocols import IAdvertCoreMapper


class ListingAdvertMapper:
    def __init__(self, core_mapper: IAdvertCoreMapper) -> None:
        self._core_mapper = core_mapper

    def map(self, advert: dict[str, Any]) -> dict[str, Any]:
        item = self._core_mapper.map(advert)
        item["address"] = advert.get("address", "")
        item["description"] = ""
        return item
