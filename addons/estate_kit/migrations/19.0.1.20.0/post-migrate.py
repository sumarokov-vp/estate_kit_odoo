"""Засевает krisha_name для районов Алматы, добавляет районы Астаны и
тестовые конфиги сбора market snapshots.

Имена районов соответствуют тому, как Krisha пишет их в HTML/jsdata
(проверено парсингом страниц krisha.kz/prodazha/kvartiry/<city>/).
"""

import logging

_logger = logging.getLogger(__name__)


_ALMATY_DISTRICTS_KRISHA_NAME = {
    "Алатауский": "Алатауский р-н",
    "Алмалинский": "Алмалинский р-н",
    "Ауэзовский": "Ауэзовский р-н",
    "Бостандыкский": "Бостандыкский р-н",
    "Жетысуский": "Жетысуский р-н",
    "Медеуский": "Медеуский р-н",
    "Наурызбайский": "Наурызбайский р-н",
    "Турксибский": "Турксибский р-н",
}

_ASTANA_DISTRICTS = [
    ("Алматинский", "Алматы р-н"),
    ("Есильский", "Есильский р-н"),
    ("Нура", "Нура р-н"),
    ("Сарайшык", "Сарайшык р-н"),
    ("Сарыарка", "Сарыарка р-н"),
]

_OBSOLETE_ALMATY_DISTRICT_DUPES = ("Бостандыкский район", "Медеуский район")


def migrate(cr, version):
    if not version:
        return

    _seed_almaty_krisha_names(cr)
    _drop_almaty_district_dupes(cr)
    _seed_astana_districts(cr)
    _seed_market_snapshot_configs(cr)


def _seed_almaty_krisha_names(cr):
    cr.execute(
        "SELECT id FROM estate_city WHERE name = 'Алматы' LIMIT 1"
    )
    row = cr.fetchone()
    if row is None:
        _logger.warning("Алматы не найден в estate_city — пропускаю seed krisha_name")
        return
    almaty_id = row[0]

    for name, krisha_name in _ALMATY_DISTRICTS_KRISHA_NAME.items():
        cr.execute(
            """
            UPDATE estate_district
            SET krisha_name = %s
            WHERE city_id = %s AND name = %s AND krisha_name IS NULL
            """,
            (krisha_name, almaty_id, name),
        )
    _logger.info("krisha_name засеян для районов Алматы")


def _drop_almaty_district_dupes(cr):
    cr.execute(
        "SELECT id FROM estate_city WHERE name = 'Алматы' LIMIT 1"
    )
    row = cr.fetchone()
    if row is None:
        return
    almaty_id = row[0]

    cr.execute(
        """
        DELETE FROM estate_district
        WHERE city_id = %s
          AND name = ANY(%s)
          AND id NOT IN (SELECT district_id FROM estate_property WHERE district_id IS NOT NULL)
        """,
        (almaty_id, list(_OBSOLETE_ALMATY_DISTRICT_DUPES)),
    )
    _logger.info("Удалены дубли районов Алматы (если были без объектов)")


def _seed_astana_districts(cr):
    cr.execute(
        "SELECT id FROM estate_city WHERE name = 'Астана' LIMIT 1"
    )
    row = cr.fetchone()
    if row is None:
        _logger.warning("Астана не найдена в estate_city — пропускаю seed районов")
        return
    astana_id = row[0]

    for name, krisha_name in _ASTANA_DISTRICTS:
        cr.execute(
            "SELECT id FROM estate_district WHERE city_id = %s AND name = %s",
            (astana_id, name),
        )
        if cr.fetchone():
            continue
        cr.execute(
            """
            INSERT INTO estate_district
                (name, krisha_name, city_id, active,
                 create_uid, write_uid, create_date, write_date)
            VALUES (%s, %s, %s, true, 1, 1, NOW(), NOW())
            """,
            (name, krisha_name, astana_id),
        )
    _logger.info("Районы Астаны добавлены")


def _seed_market_snapshot_configs(cr):
    cr.execute(
        "SELECT id, name FROM estate_city WHERE name IN ('Алматы', 'Астана')"
    )
    cities = {name: city_id for city_id, name in cr.fetchall()}
    if "Алматы" not in cities or "Астана" not in cities:
        _logger.warning("Алматы или Астана не найдены — пропускаю seed configs")
        return

    cr.execute(
        "UPDATE estate_market_snapshot_config SET max_pages = 3 WHERE max_pages = 5"
    )

    rows = []
    for city_name, city_id in cities.items():
        for property_type in ("house", "commercial", "land"):
            rows.append((city_id, None, property_type, 0, 3))

        cr.execute(
            "SELECT id FROM estate_district "
            "WHERE city_id = %s AND krisha_name IS NOT NULL",
            (city_id,),
        )
        for (district_id,) in cr.fetchall():
            rows.append((city_id, district_id, "apartment", 0, 2))

    for city_id, district_id, property_type, rooms, max_pages in rows:
        cr.execute(
            """
            SELECT id FROM estate_market_snapshot_config
            WHERE city_id = %s
              AND ((district_id IS NULL AND %s IS NULL) OR district_id = %s)
              AND property_type = %s
              AND rooms = %s
            """,
            (city_id, district_id, district_id, property_type, rooms),
        )
        if cr.fetchone():
            continue
        cr.execute(
            """
            INSERT INTO estate_market_snapshot_config
                (city_id, district_id, property_type, rooms, max_pages, active,
                 create_uid, write_uid, create_date, write_date)
            VALUES (%s, %s, %s, %s, %s, true, 1, 1, NOW(), NOW())
            """,
            (city_id, district_id, property_type, rooms, max_pages),
        )
    _logger.info("Конфиги сбора расширены: дома/коммерция/земля + районные квартиры")
