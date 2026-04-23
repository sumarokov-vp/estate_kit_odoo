from typing import Any

from .protocols import IAdvertCoreMapper


class ListingAdvertMapper:
    """Маппер для листинга: ядро + пустой description.

    На листинге Krisha не отдаёт текст объявления — description
    заполняется только при походе на страницу деталки. Все адресные
    поля формируются единообразно в ``AdvertCoreMapper``.
    """

    def __init__(self, core_mapper: IAdvertCoreMapper) -> None:
        self._core_mapper = core_mapper

    def map(self, advert: dict[str, Any]) -> dict[str, Any]:
        item = self._core_mapper.map(advert)
        item["description"] = ""
        return item
