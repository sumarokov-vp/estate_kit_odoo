from typing import Any

from .protocols import IAdvertCoreMapper


class DetailAdvertMapper:
    def __init__(self, core_mapper: IAdvertCoreMapper) -> None:
        self._core_mapper = core_mapper

    def map(self, advert: dict[str, Any]) -> dict[str, Any]:
        item = self._core_mapper.map(advert)
        item["address"] = advert.get("addressTitle", "") or advert.get("address", "")
        item["description"] = advert.get("text", "")
        return item
