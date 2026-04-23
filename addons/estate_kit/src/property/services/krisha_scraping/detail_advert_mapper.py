from typing import Any

from .protocols import IAdvertCoreMapper


class DetailAdvertMapper:
    """Маппер для страницы деталки: ядро + description из ``text``.

    Все адресные поля (``address``, ``address_title``, ``address_struct``)
    формируются в ``AdvertCoreMapper`` одинаково для листинга и деталки.
    """

    def __init__(self, core_mapper: IAdvertCoreMapper) -> None:
        self._core_mapper = core_mapper

    def map(self, advert: dict[str, Any]) -> dict[str, Any]:
        item = self._core_mapper.map(advert)
        item["description"] = advert.get("text", "")
        return item
