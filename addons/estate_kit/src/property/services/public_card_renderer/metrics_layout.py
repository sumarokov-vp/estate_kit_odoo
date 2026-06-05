"""Декларативное описание ключевых метрик карточки по типам объекта.

До 4 метрик на тип. Каждая метрика — spec вида (kind, label, args...):
    ("number", label, field, suffix)  — "{v:g}{suffix}", пропуск если пусто
    ("int", label, field)             — целое как есть, пропуск если пусто
    ("floor", label)                  — составное "floor / floors_total"
    ("selection", label, field)       — человекочитаемый label селекшена
    ("utilities", label)              — "Есть"/пропуск по наличию любой коммуникации
"""

APARTMENT_METRICS = [
    ("number", "Площадь", "area_total", " м²"),
    ("int", "Комнаты", "rooms"),
    ("floor", "Этаж"),
    ("int", "Год", "year_built"),
]

HOUSE_METRICS = [
    ("number", "Площадь дома", "area_total", " м²"),
    ("int", "Комнаты", "rooms"),
    ("number", "Участок", "area_land", " соток"),
    ("int", "Этажность", "floors_total"),
]

COMMERCIAL_METRICS = [
    ("number", "Площадь", "area_total", " м²"),
    ("floor", "Этаж"),
    ("selection", "Назначение", "building_type"),
    ("int", "Год", "year_built"),
]

LAND_METRICS = [
    ("number", "Площадь участка", "area_land", " соток"),
    ("selection", "Назначение", "building_type"),
    ("utilities", "Коммуникации"),
]

METRICS_BY_TYPE = {
    "apartment": APARTMENT_METRICS,
    "house": HOUSE_METRICS,
    "townhouse": HOUSE_METRICS,
    "commercial": COMMERCIAL_METRICS,
    "land": LAND_METRICS,
}

UTILITY_FIELDS = ("gas", "water", "sewage", "electricity")
