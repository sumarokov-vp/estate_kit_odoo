from typing import Any

from .config import BASE_URL
from .protocols import IAreaExtractor, IRoomsExtractor


class AdvertCoreMapper:
    """Маппер общих полей Krisha-объявления из сырого JSON.

    Возвращает словарь-ядро, одинаковый для листинга и деталки:
    идентификаторы, url, title, rooms, area, price, координаты,
    photo_urls, city, residential_complex и нормализованный address.

    Контракт адресных полей (общий для листинга и деталки):

    - ``address`` — строка (``addressTitle`` или пустая строка,
      никогда не dict).
    - ``address_title`` — строка с человекочитаемым адресом из
      ``addressTitle``.
    - ``address_struct`` — dict из исходного ``advert["address"]``
      (``city``, ``street``, ``house_num``, ...) или пустой dict,
      если Krisha вернула строку/None.

    Поля ``floor`` и ``floors_total`` всегда ``None`` на уровне core:
    в сыром JSON Krisha их нет, они заполняются только HTML-парсером
    (``AdvertInfoHtmlExtractor``) при заходе на страницу деталки.
    """

    def __init__(
        self,
        rooms_extractor: IRoomsExtractor,
        area_extractor: IAreaExtractor,
    ) -> None:
        self._rooms_extractor = rooms_extractor
        self._area_extractor = area_extractor

    def map(self, advert: dict[str, Any]) -> dict[str, Any]:
        photo_urls = [
            photo.get("src", "").replace("-thumb", "-full")
            for photo in advert.get("photos", [])
            if photo.get("src")
        ]

        map_data = advert.get("map", {})
        lat = map_data.get("lat")
        lon = map_data.get("lon")

        address_raw = advert.get("address")
        address_struct = address_raw if isinstance(address_raw, dict) else {}
        city = address_struct.get("city", "") or ""

        address_title_raw = advert.get("addressTitle")
        address_title = address_title_raw if isinstance(address_title_raw, str) else ""
        address = address_title or (address_raw if isinstance(address_raw, str) else "")

        krisha_complex_id = advert.get("complexId")
        complex_name = advert.get("complexName")

        title = advert.get("title", "")

        return {
            "krisha_id": advert.get("id"),
            "url": f"{BASE_URL}/a/show/{advert.get('id')}",
            "title": title,
            "rooms": self._rooms_extractor.extract(title),
            "area": self._area_extractor.extract(advert.get("square")),
            "floor": None,
            "floors_total": None,
            "price": advert.get("price"),
            "city": city,
            "latitude": float(lat) if lat else None,
            "longitude": float(lon) if lon else None,
            "photo_urls": photo_urls,
            "krisha_complex_id": int(krisha_complex_id) if krisha_complex_id else None,
            "residential_complex_name": complex_name if isinstance(complex_name, str) else None,
            "address": address,
            "address_title": address_title,
            "address_struct": address_struct,
        }
