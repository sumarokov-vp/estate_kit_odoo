"""Декларативное описание разделов карточки.

Каждый раздел: title, icon, список строк (rows).
Каждая строка — spec вида (kind, args...):
    ("number", field, label, suffix)   — числовое поле, формат "{v:g}{suffix}"
    ("int", field, label)              — целочисленное поле как есть
    ("floor", label)                   — составное "floor / floors_total"
    ("selection", field, label)        — человекочитаемый label селекшена
    ("bool", field, label)             — булево, значение "Да" если True, иначе пропуск

Разделы с привязкой к типам объектов фильтруются по property_types
(None — для всех типов).
"""

PARAMETERS_SECTION = {
    "title": "Параметры",
    "icon": "📐",
    "property_types": None,
    "rows": [
        ("number", "area_total", "Общая площадь, м²", ""),
        ("number", "area_living", "Жилая, м²", ""),
        ("number", "area_kitchen", "Кухня, м²", ""),
        ("int", "rooms", "Комнат"),
        ("int", "bedrooms", "Спален"),
        ("floor", "Этаж"),
        ("int", "year_built", "Год постройки"),
        ("selection", "building_type", "Тип строения"),
        ("selection", "wall_material", "Материал стен"),
        ("number", "ceiling_height", "Высота потолков, м", ""),
    ],
}

TERRITORY_SECTION = {
    "title": "Территория",
    "icon": "🌿",
    "property_types": ("house", "townhouse", "land"),
    "rows": [
        ("number", "area_land", "Площадь участка, соток", ""),
    ],
}

COMFORT_SECTION = {
    "title": "Комфорт",
    "icon": "🛋",
    "property_types": None,
    "rows": [
        ("selection", "condition", "Состояние"),
        ("selection", "bathroom", "Санузел"),
        ("int", "bathroom_count", "Кол-во санузлов"),
        ("selection", "balcony", "Балкон"),
        ("selection", "parking", "Парковка"),
        ("selection", "furniture", "Мебель"),
        ("selection", "heating", "Отопление"),
    ],
}

SECURITY_SECTION = {
    "title": "Безопасность",
    "icon": "🔒",
    "property_types": None,
    "rows": [
        ("bool", "security_video", "Видеонаблюдение"),
        ("bool", "security_guard", "Охрана"),
        ("bool", "security_intercom", "Домофон"),
        ("bool", "security_concierge", "Консьерж"),
    ],
}

UTILITIES_SECTION = {
    "title": "Коммуникации",
    "icon": "⚙️",
    "property_types": None,
    "rows": [
        ("selection", "gas", "Газ"),
        ("selection", "water", "Водоснабжение"),
        ("selection", "sewage", "Канализация"),
        ("selection", "internet", "Интернет"),
    ],
}

SECTIONS: list[dict] = [
    PARAMETERS_SECTION,
    TERRITORY_SECTION,
    COMFORT_SECTION,
    SECURITY_SECTION,
    UTILITIES_SECTION,
]
