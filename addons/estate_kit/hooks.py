import logging

_logger = logging.getLogger(__name__)


def post_init_hook(env):
    _init_cities(env)
    _init_districts(env)
    _init_sources(env)


def _init_cities(env):
    cities = [
        {"name": "Алматы", "code": "almaty", "sequence": 1},
        {"name": "Астана", "code": "astana", "sequence": 2},
        {"name": "Шымкент", "code": "shymkent", "sequence": 3},
        {"name": "Актобе", "code": "aktobe", "sequence": 10},
        {"name": "Караганда", "code": "karaganda", "sequence": 11},
        {"name": "Тараз", "code": "taraz", "sequence": 12},
        {"name": "Павлодар", "code": "pavlodar", "sequence": 13},
        {"name": "Усть-Каменогорск", "code": "ust-kamenogorsk", "sequence": 14},
        {"name": "Семей", "code": "semey", "sequence": 15},
        {"name": "Атырау", "code": "atyrau", "sequence": 16},
        {"name": "Костанай", "code": "kostanay", "sequence": 17},
        {"name": "Кызылорда", "code": "kyzylorda", "sequence": 18},
        {"name": "Уральск", "code": "uralsk", "sequence": 19},
        {"name": "Петропавловск", "code": "petropavlovsk", "sequence": 20},
        {"name": "Актау", "code": "aktau", "sequence": 21},
        {"name": "Темиртау", "code": "temirtau", "sequence": 22},
        {"name": "Туркестан", "code": "turkestan", "sequence": 23},
        {"name": "Кокшетау", "code": "kokshetau", "sequence": 24},
        {"name": "Талдыкорган", "code": "taldykorgan", "sequence": 25},
        {"name": "Экибастуз", "code": "ekibastuz", "sequence": 26},
        {"name": "Рудный", "code": "rudny", "sequence": 27},
        {"name": "Жанаозен", "code": "zhanaozen", "sequence": 28},
        {"name": "Жезказган", "code": "zhezkazgan", "sequence": 29},
        {"name": "Балхаш", "code": "balkhash", "sequence": 30},
        {"name": "Кентау", "code": "kentau", "sequence": 31},
        {"name": "Сатпаев", "code": "satpayev", "sequence": 32},
        {"name": "Каскелен", "code": "kaskelen", "sequence": 33},
        {"name": "Конаев", "code": "konayev", "sequence": 34},
    ]
    City = env["estate.city"]
    existing_codes = set(City.search([]).mapped("code"))
    to_create = [c for c in cities if c["code"] not in existing_codes]
    if to_create:
        City.create(to_create)
        _logger.info("Created %d cities", len(to_create))


def _init_districts(env):
    almaty = env["estate.city"].search([("code", "=", "almaty")], limit=1)
    if not almaty:
        _logger.warning("City Almaty not found, skipping districts init")
        return

    districts = [
        {"name": "Алатауский", "code": "alatau", "city_id": almaty.id},
        {"name": "Алмалинский", "code": "almaly", "city_id": almaty.id},
        {"name": "Ауэзовский", "code": "auezov", "city_id": almaty.id},
        {"name": "Бостандыкский", "code": "bostandyk", "city_id": almaty.id},
        {"name": "Жетысуский", "code": "zhetysu", "city_id": almaty.id},
        {"name": "Медеуский", "code": "medeu", "city_id": almaty.id},
        {"name": "Наурызбайский", "code": "nauryzbay", "city_id": almaty.id},
        {"name": "Турксибский", "code": "turksib", "city_id": almaty.id},
    ]
    District = env["estate.district"]
    existing = {d.code: d for d in District.search([])}

    to_create = []
    for data in districts:
        if data["code"] in existing:
            district = existing[data["code"]]
            if not district.city_id:
                district.write({"city_id": almaty.id})
                _logger.info("Updated district with city: %s", data["name"])
        else:
            to_create.append(data)

    if to_create:
        District.create(to_create)
        _logger.info("Created %d districts", len(to_create))


def _init_sources(env):
    sources = [
        {"name": "Крыша.kz", "code": "krysha", "sequence": 10},
        {"name": "OLX", "code": "olx", "sequence": 20},
        {"name": "Рекомендация", "code": "referral", "sequence": 30},
        {"name": "Холодный звонок", "code": "cold_call", "sequence": 40},
        {"name": "Вывеска", "code": "sign", "sequence": 50},
        {"name": "Соцсети", "code": "social", "sequence": 60},
        {"name": "Сайт", "code": "website", "sequence": 70},
        {"name": "Telegram-бот", "code": "telegram_bot", "sequence": 80},
    ]
    Source = env["estate.source"]
    existing_codes = set(Source.search([]).mapped("code"))
    to_create = [s for s in sources if s["code"] not in existing_codes]
    if to_create:
        Source.create(to_create)
        _logger.info("Created %d sources", len(to_create))
