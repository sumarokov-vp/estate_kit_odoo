from typing import Any

from .protocols import IAdvertCoreMapper


class DetailAdvertMapper:
    def __init__(self, core_mapper: IAdvertCoreMapper) -> None:
        self._core_mapper = core_mapper

    def map(self, advert: dict[str, Any]) -> dict[str, Any]:
        item = self._core_mapper.map(advert)

        address_title = advert.get("addressTitle") or ""
        address_raw = advert.get("address")
        address_struct = address_raw if isinstance(address_raw, dict) else {}

        item["address_title"] = address_title if isinstance(address_title, str) else ""
        item["address_struct"] = address_struct
        item["address"] = item["address_title"] or (
            address_raw if isinstance(address_raw, str) else ""
        )
        item["description"] = advert.get("text", "")
        return item
