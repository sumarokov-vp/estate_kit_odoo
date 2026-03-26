PROPERTY_TYPE_LABELS = {
    "apartment": "Квартира",
    "house": "Дом",
    "townhouse": "Таунхаус",
    "commercial": "Коммерция",
    "land": "Земля",
}

DEAL_TYPE_LABELS = {
    "sale": "Продажа",
    "rent_long": "Долгосрочная аренда",
    "rent_daily": "Посуточная аренда",
}

CONDITION_LABELS = {
    "no_repair": "Без ремонта",
    "cosmetic": "Косметический",
    "euro": "Евроремонт",
    "designer": "Дизайнерский",
}

SELECTION_LABELS = {
    "property_type": PROPERTY_TYPE_LABELS,
    "deal_type": DEAL_TYPE_LABELS,
    "condition": CONDITION_LABELS,
    "building_type": {
        "panel": "Панельный",
        "brick": "Кирпичный",
        "monolith": "Монолит",
        "metal_frame": "Металлокаркас",
        "wood": "Деревянный",
    },
    "wall_material": {
        "brick": "Кирпич",
        "gas_block": "Газоблок",
        "wood": "Дерево",
        "sip": "СИП-панели",
        "frame": "Каркас",
        "polystyrene": "Полистиролбетон",
    },
    "roof_type": {"flat": "Плоская", "gable": "Двускатная", "hip": "Вальмовая"},
    "foundation": {"strip": "Ленточный", "slab": "Плитный", "pile": "Свайный"},
    "bathroom": {"combined": "Совмещённый", "separate": "Раздельный"},
    "balcony": {
        "none": "Нет",
        "balcony": "Балкон",
        "loggia": "Лоджия",
        "terrace": "Терраса",
    },
    "parking": {
        "none": "Нет",
        "yard": "Двор",
        "underground": "Подземная",
        "garage": "Гараж",
        "ground": "Наземная",
    },
    "furniture": {"none": "Без мебели", "partial": "Частично", "full": "Полная"},
    "heating": {"central": "Центральное", "autonomous": "Автономное", "none": "Нет"},
    "water": {"central": "Центральное", "well": "Скважина", "none": "Нет"},
    "sewage": {"central": "Центральная", "septic": "Септик", "none": "Нет"},
    "gas": {"central": "Центральный", "balloon": "Баллонный", "none": "Нет"},
    "electricity": {"yes": "Есть", "nearby": "Рядом", "none": "Нет"},
    "commercial_type": {
        "office": "Офис",
        "retail": "Торговое",
        "warehouse": "Склад",
        "production": "Производство",
    },
    "land_category": {
        "izhs": "ИЖС",
        "snt": "СНТ",
        "lpkh": "ЛПХ",
        "commercial": "Коммерческое",
    },
    "land_status": {"owned": "В собственности", "leased": "Аренда"},
    "road_access": {
        "asphalt": "Асфальт",
        "gravel": "Гравий",
        "dirt": "Грунтовая",
        "none": "Нет",
    },
}
