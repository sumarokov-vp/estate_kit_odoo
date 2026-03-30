import logging

_logger = logging.getLogger(__name__)

CITIES = [
    ("almaty", "Алматы", 1),
    ("astana", "Астана", 2),
    ("shymkent", "Шымкент", 3),
    ("almaty_oblast", "Алматинская область", 4),
    ("aktobe", "Актобе", 10),
    ("karaganda", "Караганда", 11),
    ("taraz", "Тараз", 12),
    ("pavlodar", "Павлодар", 13),
    ("ust-kamenogorsk", "Усть-Каменогорск", 14),
    ("semey", "Семей", 15),
    ("atyrau", "Атырау", 16),
    ("kostanay", "Костанай", 17),
    ("kyzylorda", "Кызылорда", 18),
    ("uralsk", "Уральск", 19),
    ("petropavlovsk", "Петропавловск", 20),
    ("aktau", "Актау", 21),
    ("temirtau", "Темиртау", 22),
    ("turkestan", "Туркестан", 23),
    ("kokshetau", "Кокшетау", 24),
    ("taldykorgan", "Талдыкорган", 25),
    ("ekibastuz", "Экибастуз", 26),
    ("rudny", "Рудный", 27),
    ("zhanaozen", "Жанаозен", 28),
    ("zhezkazgan", "Жезказган", 29),
    ("balkhash", "Балхаш", 30),
    ("kentau", "Кентау", 31),
    ("satpayev", "Сатпаев", 32),
    ("kaskelen", "Каскелен", 33),
    ("konayev", "Конаев", 34),
]

DISTRICTS = [
    ("alatau", "Алатауский"),
    ("almaly", "Алмалинский"),
    ("auezov", "Ауэзовский"),
    ("bostandyk", "Бостандыкский"),
    ("zhetysu", "Жетысуский"),
    ("medeu", "Медеуский"),
    ("nauryzbay", "Наурызбайский"),
    ("turksib", "Турксибский"),
]

SOURCES = [
    ("krysha", "Крыша.kz", 10),
    ("olx", "OLX", 20),
    ("referral", "Рекомендация", 30),
    ("cold_call", "Холодный звонок", 40),
    ("sign", "Вывеска", 50),
    ("social", "Соцсети", 60),
    ("website", "Сайт", 70),
    ("telegram_bot", "Telegram-бот", 80),
]


def migrate(cr, version):
    if not version:
        return

    _logger.info("Migration 19.0.1.8.0: seed reference data")
    _seed_cities(cr)
    _seed_districts(cr)
    _seed_sources(cr)
    _normalize_city_names(cr)
    _apply_erp_core_migrations()


def _seed_cities(cr):
    cr.execute("SELECT code FROM estate_city")
    existing = {row[0] for row in cr.fetchall()}

    to_create = [(code, name, seq) for code, name, seq in CITIES if code not in existing]
    for code, name, seq in to_create:
        cr.execute(
            "INSERT INTO estate_city (code, name, sequence, create_uid, create_date, write_uid, write_date) "
            "VALUES (%s, %s, %s, 1, NOW(), 1, NOW())",
            (code, name, seq),
        )
    if to_create:
        _logger.info("Created %d cities", len(to_create))


def _seed_districts(cr):
    cr.execute("SELECT id FROM estate_city WHERE code = 'almaty' LIMIT 1")
    row = cr.fetchone()
    if not row:
        _logger.warning("City Almaty not found, skipping districts")
        return
    almaty_id = row[0]

    cr.execute("SELECT code FROM estate_district")
    existing = {row[0] for row in cr.fetchall()}

    to_create = [(code, name) for code, name in DISTRICTS if code not in existing]
    for code, name in to_create:
        cr.execute(
            "INSERT INTO estate_district (code, name, city_id, create_uid, create_date, write_uid, write_date) "
            "VALUES (%s, %s, %s, 1, NOW(), 1, NOW())",
            (code, name, almaty_id),
        )

    # Update existing districts without city_id
    cr.execute(
        "UPDATE estate_district SET city_id = %s WHERE code IN %s AND city_id IS NULL",
        (almaty_id, tuple(code for code, _ in DISTRICTS)),
    )

    if to_create:
        _logger.info("Created %d districts", len(to_create))


def _seed_sources(cr):
    cr.execute("SELECT code FROM estate_source")
    existing = {row[0] for row in cr.fetchall()}

    to_create = [(code, name, seq) for code, name, seq in SOURCES if code not in existing]
    for code, name, seq in to_create:
        cr.execute(
            "INSERT INTO estate_source (code, name, sequence, create_uid, create_date, write_uid, write_date) "
            "VALUES (%s, %s, %s, 1, NOW(), 1, NOW())",
            (code, name, seq),
        )
    if to_create:
        _logger.info("Created %d sources", len(to_create))


def _normalize_city_names(cr):
    """Remove 'г. ' prefix from city names added by old XML data."""
    cr.execute(
        "UPDATE estate_city SET name = REGEXP_REPLACE(name, '^г\\.\\s*', '') "
        "WHERE name LIKE 'г. %'"
    )
    if cr.rowcount:
        _logger.info("Normalized %d city names", cr.rowcount)


def _apply_erp_core_migrations():
    try:
        from odoo.addons.estate_kit.src.erp_core.services.initializer.factory import Factory

        Factory.create().initialize()
    except Exception as e:
        _logger.warning("ERP Core migrations skipped: %s", e)
