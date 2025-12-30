import json
import logging

_logger = logging.getLogger(__name__)


def post_init_hook(env):
    _init_districts(env)
    _init_sources(env)
    _init_attributes(env)


def _init_districts(env):
    districts = [
        {"name": "Алатауский", "code": "alatau"},
        {"name": "Алмалинский", "code": "almaly"},
        {"name": "Ауэзовский", "code": "auezov"},
        {"name": "Бостандыкский", "code": "bostandyk"},
        {"name": "Жетысуский", "code": "zhetysu"},
        {"name": "Медеуский", "code": "medeu"},
        {"name": "Наурызбайский", "code": "nauryzbay"},
        {"name": "Турксибский", "code": "turksib"},
    ]
    District = env["estate.district"]
    for data in districts:
        if not District.search([("code", "=", data["code"])], limit=1):
            District.create(data)
            _logger.info(f"Created district: {data['name']}")


def _init_sources(env):
    sources = [
        {"name": "Крыша.kz", "code": "krysha", "sequence": 10},
        {"name": "OLX", "code": "olx", "sequence": 20},
        {"name": "Рекомендация", "code": "referral", "sequence": 30},
        {"name": "Холодный звонок", "code": "cold_call", "sequence": 40},
        {"name": "Вывеска", "code": "sign", "sequence": 50},
        {"name": "Соцсети", "code": "social", "sequence": 60},
        {"name": "Сайт", "code": "website", "sequence": 70},
    ]
    Source = env["estate.source"]
    for data in sources:
        if not Source.search([("code", "=", data["code"])], limit=1):
            Source.create(data)
            _logger.info(f"Created source: {data['name']}")


def _init_attributes(env):
    attributes = [
        # Construction
        {"name": "Этаж", "code": "floor", "field_type": "integer", "category": "construction", "property_types": "apartment", "sequence": 10, "is_filterable": True},
        {"name": "Этажность дома", "code": "floors_total", "field_type": "integer", "category": "construction", "property_types": "apartment,house", "sequence": 20, "is_filterable": True},
        {"name": "Год постройки", "code": "year_built", "field_type": "integer", "category": "construction", "property_types": "all", "sequence": 30, "is_filterable": True},
        {"name": "Тип строения", "code": "building_type", "field_type": "selection", "category": "construction", "property_types": "all", "sequence": 40, "is_filterable": True, "selection_options": json.dumps([
            {"value": "panel", "label": "Панельный"},
            {"value": "brick", "label": "Кирпичный"},
            {"value": "monolith", "label": "Монолитный"},
            {"value": "block", "label": "Блочный"},
            {"value": "wood", "label": "Деревянный"},
        ])},
        {"name": "Материал стен", "code": "wall_material", "field_type": "selection", "category": "construction", "property_types": "house", "sequence": 50, "selection_options": json.dumps([
            {"value": "brick", "label": "Кирпич"},
            {"value": "block", "label": "Блок"},
            {"value": "wood", "label": "Дерево"},
            {"value": "sip", "label": "СИП-панели"},
        ])},
        {"name": "Состояние", "code": "condition", "field_type": "selection", "category": "construction", "property_types": "all", "sequence": 60, "is_filterable": True, "selection_options": json.dumps([
            {"value": "new", "label": "Новостройка"},
            {"value": "good", "label": "Хорошее"},
            {"value": "needs_repair", "label": "Требует ремонта"},
            {"value": "rough", "label": "Черновая отделка"},
        ])},
        # Area
        {"name": "Жилая площадь", "code": "area_living", "field_type": "float", "category": "area", "property_types": "apartment,house", "sequence": 10},
        {"name": "Площадь кухни", "code": "area_kitchen", "field_type": "float", "category": "area", "property_types": "apartment,house", "sequence": 20},
        {"name": "Площадь участка", "code": "area_land", "field_type": "float", "category": "area", "property_types": "house,land", "sequence": 30},
        # Utilities
        {"name": "Отопление", "code": "heating", "field_type": "selection", "category": "utilities", "property_types": "apartment,house,commercial", "sequence": 10, "selection_options": json.dumps([
            {"value": "central", "label": "Центральное"},
            {"value": "individual", "label": "Индивидуальное"},
            {"value": "none", "label": "Нет"},
        ])},
        {"name": "Газ", "code": "gas", "field_type": "boolean", "category": "utilities", "property_types": "all", "sequence": 20},
        {"name": "Вода", "code": "water", "field_type": "boolean", "category": "utilities", "property_types": "all", "sequence": 30},
        {"name": "Канализация", "code": "sewage", "field_type": "boolean", "category": "utilities", "property_types": "all", "sequence": 40},
        {"name": "Электричество", "code": "electricity", "field_type": "boolean", "category": "utilities", "property_types": "all", "sequence": 50},
        # Amenities
        {"name": "Санузел", "code": "bathroom", "field_type": "selection", "category": "amenities", "property_types": "apartment,house", "sequence": 10, "selection_options": json.dumps([
            {"value": "combined", "label": "Совмещённый"},
            {"value": "separate", "label": "Раздельный"},
            {"value": "two_plus", "label": "2 и более"},
        ])},
        {"name": "Балкон", "code": "balcony", "field_type": "boolean", "category": "amenities", "property_types": "apartment", "sequence": 20, "is_filterable": True},
        {"name": "Лоджия", "code": "loggia", "field_type": "boolean", "category": "amenities", "property_types": "apartment", "sequence": 30},
        {"name": "Лифт", "code": "elevator", "field_type": "boolean", "category": "amenities", "property_types": "apartment", "sequence": 40},
        {"name": "Мебель", "code": "furniture", "field_type": "boolean", "category": "amenities", "property_types": "apartment,house", "sequence": 50, "is_filterable": True},
        {"name": "Кондиционер", "code": "air_conditioning", "field_type": "boolean", "category": "amenities", "property_types": "apartment,house,commercial", "sequence": 60},
        {"name": "Интернет", "code": "internet", "field_type": "boolean", "category": "amenities", "property_types": "apartment,house,commercial", "sequence": 70},
        # Security
        {"name": "Домофон", "code": "intercom", "field_type": "boolean", "category": "security", "property_types": "apartment", "sequence": 10},
        {"name": "Видеонаблюдение", "code": "cctv", "field_type": "boolean", "category": "security", "property_types": "all", "sequence": 20},
        {"name": "Охрана", "code": "security_guard", "field_type": "boolean", "category": "security", "property_types": "all", "sequence": 30},
        {"name": "Парковка", "code": "parking", "field_type": "selection", "category": "security", "property_types": "all", "sequence": 40, "is_filterable": True, "selection_options": json.dumps([
            {"value": "none", "label": "Нет"},
            {"value": "yard", "label": "Во дворе"},
            {"value": "underground", "label": "Подземная"},
            {"value": "garage", "label": "Гараж"},
        ])},
        # Legal
        {"name": "В залоге", "code": "is_pledged", "field_type": "boolean", "category": "legal", "property_types": "all", "sequence": 10, "is_filterable": True},
        {"name": "Под арестом", "code": "is_arrested", "field_type": "boolean", "category": "legal", "property_types": "all", "sequence": 20},
        {"name": "Обременение", "code": "encumbrance", "field_type": "char", "category": "legal", "property_types": "all", "sequence": 30},
        {"name": "Правоустанавливающий документ", "code": "title_document", "field_type": "selection", "category": "legal", "property_types": "all", "sequence": 40, "selection_options": json.dumps([
            {"value": "purchase", "label": "Договор купли-продажи"},
            {"value": "privatization", "label": "Приватизация"},
            {"value": "inheritance", "label": "Наследство"},
            {"value": "gift", "label": "Дарение"},
            {"value": "construction", "label": "Акт ввода в эксплуатацию"},
        ])},
        # Commercial
        {"name": "Назначение", "code": "commercial_purpose", "field_type": "selection", "category": "commercial", "property_types": "commercial", "sequence": 10, "is_filterable": True, "selection_options": json.dumps([
            {"value": "office", "label": "Офис"},
            {"value": "retail", "label": "Торговое"},
            {"value": "warehouse", "label": "Склад"},
            {"value": "production", "label": "Производство"},
            {"value": "catering", "label": "Общепит"},
            {"value": "service", "label": "Сфера услуг"},
        ])},
        {"name": "Витринные окна", "code": "storefront", "field_type": "boolean", "category": "commercial", "property_types": "commercial", "sequence": 20},
        {"name": "Отдельный вход", "code": "separate_entrance", "field_type": "boolean", "category": "commercial", "property_types": "commercial", "sequence": 30},
        # Land
        {"name": "Категория земли", "code": "land_category", "field_type": "selection", "category": "land", "property_types": "land", "sequence": 10, "is_filterable": True, "selection_options": json.dumps([
            {"value": "izhs", "label": "ИЖС"},
            {"value": "lph", "label": "ЛПХ"},
            {"value": "snt", "label": "СНТ"},
            {"value": "commercial", "label": "Коммерческое"},
            {"value": "agricultural", "label": "Сельхозназначение"},
        ])},
        {"name": "Форма участка", "code": "land_shape", "field_type": "selection", "category": "land", "property_types": "land,house", "sequence": 20, "selection_options": json.dumps([
            {"value": "rectangular", "label": "Прямоугольный"},
            {"value": "square", "label": "Квадратный"},
            {"value": "irregular", "label": "Неправильной формы"},
        ])},
    ]
    Attribute = env["estate.attribute"]
    for data in attributes:
        if not Attribute.search([("code", "=", data["code"])], limit=1):
            Attribute.create(data)
            _logger.info(f"Created attribute: {data['name']}")
