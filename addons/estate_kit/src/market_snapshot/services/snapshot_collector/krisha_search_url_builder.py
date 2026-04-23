from urllib.parse import urlencode

from .config import SnapshotTarget

_BASE_URL = "https://krisha.kz"

_CATEGORY_SLUG: dict[str, str] = {
    "apartment": "prodazha/kvartiry",
    "house": "prodazha/doma",
    "townhouse": "prodazha/doma",
    "commercial": "prodazha/kommercheskaya-nedvizhimost",
    "land": "prodazha/uchastkov",
}

_CITY_SLUG: dict[str, str] = {
    "Алматы": "almaty",
    "Астана": "astana",
    "Нур-Султан": "astana",
    "Шымкент": "shymkent",
    "Актобе": "aktobe",
    "Караганда": "karaganda",
    "Павлодар": "pavlodar",
    "Усть-Каменогорск": "ust-kamenogorsk",
    "Атырау": "atyrau",
    "Костанай": "kostanay",
    "Семей": "semey",
    "Кызылорда": "kyzylorda",
    "Уральск": "uralsk",
    "Петропавловск": "petropavlovsk",
    "Актау": "aktau",
    "Туркестан": "turkistan",
    "Тараз": "taraz",
    "Кокшетау": "kokshetau",
    "Талдыкорган": "taldykorgan",
    "Экибастуз": "ekibastuz",
}


class KrishaSearchUrlBuilder:
    def build(self, target: SnapshotTarget) -> str | None:
        category = _CATEGORY_SLUG.get(target.property_type)
        city_slug = _CITY_SLUG.get(target.city_name)
        if not category or not city_slug:
            return None

        path_parts = [category, city_slug]
        url = f"{_BASE_URL}/{'/'.join(path_parts)}/"

        params: list[tuple[str, str]] = []
        if target.rooms and target.rooms > 0:
            params.append(("das[live.rooms][]", str(target.rooms)))
        if target.district_name:
            params.append(("das[map.district]", target.district_name))

        if params:
            url = f"{url}?{urlencode(params)}"
        return url
