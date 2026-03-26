PROPERTY_TYPE_LABELS = {
    "apartment": "Квартира",
    "house": "Дом",
    "townhouse": "Таунхаус",
    "commercial": "Коммерция",
    "land": "Земля",
}

ODOO_TO_API_PROPERTY_TYPE = PROPERTY_TYPE_LABELS

API_PROPERTY_TYPE_MAP = {i: key for i, key in enumerate(PROPERTY_TYPE_LABELS, start=1)}

ODOO_TO_API_DEAL_TYPE = {
    "sale": "Продажа",
    "rent_long": "Долгосрочная аренда",
    "rent_daily": "Посуточная аренда",
}
