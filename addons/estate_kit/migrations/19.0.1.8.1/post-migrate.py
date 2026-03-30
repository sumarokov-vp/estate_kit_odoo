import logging

_logger = logging.getLogger(__name__)

CITY_XMLIDS = {
    "almaty": "city_almaty",
    "astana": "city_astana",
    "shymkent": "city_shymkent",
    "almaty_oblast": "city_almaty_oblast",
    "aktobe": "city_aktobe",
    "karaganda": "city_karaganda",
    "taraz": "city_taraz",
    "pavlodar": "city_pavlodar",
    "ust-kamenogorsk": "city_ust_kamenogorsk",
    "semey": "city_semey",
    "atyrau": "city_atyrau",
    "kostanay": "city_kostanay",
    "kyzylorda": "city_kyzylorda",
    "uralsk": "city_uralsk",
    "petropavlovsk": "city_petropavlovsk",
    "aktau": "city_aktau",
    "temirtau": "city_temirtau",
    "turkestan": "city_turkestan",
    "kokshetau": "city_kokshetau",
    "taldykorgan": "city_taldykorgan",
    "ekibastuz": "city_ekibastuz",
    "rudny": "city_rudny",
    "zhanaozen": "city_zhanaozen",
    "zhezkazgan": "city_zhezkazgan",
    "balkhash": "city_balkhash",
    "kentau": "city_kentau",
    "satpayev": "city_satpayev",
    "kaskelen": "city_kaskelen",
    "konayev": "city_konayev",
}

DISTRICT_XMLIDS = {
    "alatau": "district_alatau",
    "almaly": "district_almaly",
    "auezov": "district_auezov",
    "bostandyk": "district_bostandyk",
    "zhetysu": "district_zhetysu",
    "medeu": "district_medeu",
    "nauryzbay": "district_nauryzbay",
    "turksib": "district_turksib",
}

SOURCE_XMLIDS = {
    "krysha": "source_krysha",
    "olx": "source_olx",
    "referral": "source_referral",
    "cold_call": "source_cold_call",
    "sign": "source_sign",
    "social": "source_social",
    "website": "source_website",
    "telegram_bot": "source_telegram_bot",
}


def migrate(cr, version):
    if not version:
        return

    _logger.info("Migration 19.0.1.8.1: deduplicate reference data")
    _dedup_table(cr, "estate_city", "estate.city", "code", CITY_XMLIDS)
    _dedup_table(cr, "estate_district", "estate.district", "code", DISTRICT_XMLIDS)
    _dedup_table(cr, "estate_source", "estate.source", "code", SOURCE_XMLIDS)


def _dedup_table(cr, table, model, key_column, xmlid_map):
    """For each duplicate code: keep the oldest record, reassign xmlid to it, delete newer duplicates."""
    cr.execute(f"""
        SELECT {key_column} FROM {table}
        GROUP BY {key_column} HAVING COUNT(*) > 1
    """)
    dup_codes = [row[0] for row in cr.fetchall()]
    if not dup_codes:
        return

    removed = 0
    for code in dup_codes:
        # Find all records with this code, oldest first
        cr.execute(
            f"SELECT id FROM {table} WHERE {key_column} = %s ORDER BY id",
            (code,),
        )
        ids = [row[0] for row in cr.fetchall()]
        if len(ids) < 2:
            continue
        keep_id = ids[0]  # oldest record (has FK references)
        delete_ids = ids[1:]

        # Reassign xmlid to the oldest record
        xmlid_name = xmlid_map.get(code)
        if xmlid_name:
            cr.execute(
                "UPDATE ir_model_data SET res_id = %s "
                "WHERE module = 'estate_kit' AND name = %s AND model = %s",
                (keep_id, xmlid_name, model),
            )

        # Delete newer duplicates
        cr.execute(
            f"DELETE FROM {table} WHERE id IN %s",
            (tuple(delete_ids),),
        )
        removed += len(delete_ids)

    _logger.info("Removed %d duplicate rows from %s", removed, table)
