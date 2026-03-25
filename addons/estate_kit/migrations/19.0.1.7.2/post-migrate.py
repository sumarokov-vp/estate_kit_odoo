import json
import logging

_logger = logging.getLogger(__name__)

STAGE_MAPPING = {
    "crm.stage_lead1": {"name_en": "New", "name_ru": "Новое"},
    "crm.stage_lead2": {"name_en": "Qualified", "name_ru": "Квалифицирован"},
    "crm.stage_lead3": {"name_en": "Proposition", "name_ru": "Предложение"},
    "crm.stage_lead4": {"name_en": "Won", "name_ru": "Выиграно"},
}

ESTATE_STAGES = {
    "estate_kit.crm_stage_matched": {"name_en": "Matched", "name_ru": "Подобрано", "sequence": 3},
    "estate_kit.crm_stage_viewing": {"name_en": "Viewing", "name_ru": "Просмотр", "sequence": 4},
    "estate_kit.crm_stage_negotiation": {"name_en": "Negotiation", "name_ru": "Переговоры", "sequence": 5},
}

DUPLICATES = [
    "estate_kit.crm_stage_new",
    "estate_kit.crm_stage_qualified",
    "estate_kit.crm_stage_proposal",
]

DUPLICATE_TARGETS = {
    "estate_kit.crm_stage_new": "crm.stage_lead1",
    "estate_kit.crm_stage_qualified": "crm.stage_lead2",
    "estate_kit.crm_stage_proposal": "crm.stage_lead3",
}


def migrate(cr, version):
    if not version:
        return

    _logger.info("Migration 19.0.1.7.2: normalizing CRM stages")

    duplicate_ids = _resolve_xmlids(cr, DUPLICATES)
    target_ids = _resolve_xmlids(cr, list(DUPLICATE_TARGETS.values()))

    for dup_xmlid, target_xmlid in DUPLICATE_TARGETS.items():
        dup_id = duplicate_ids.get(dup_xmlid)
        target_id = target_ids.get(target_xmlid)
        if dup_id and target_id:
            cr.execute(
                "UPDATE crm_lead SET stage_id = %s WHERE stage_id = %s",
                (target_id, dup_id),
            )
            _logger.info("Migration 19.0.1.7.2: moved leads from stage %s to %s", dup_id, target_id)

    for dup_xmlid in DUPLICATES:
        dup_id = duplicate_ids.get(dup_xmlid)
        if dup_id:
            cr.execute(
                "DELETE FROM ir_model_data WHERE res_id = %s AND model = 'crm.stage' AND module = %s",
                (dup_id, "estate_kit"),
            )
            cr.execute("DELETE FROM crm_stage WHERE id = %s", (dup_id,))
            _logger.info("Migration 19.0.1.7.2: deleted duplicate stage %s", dup_xmlid)

    stage_ids = _resolve_xmlids(cr, list(STAGE_MAPPING.keys()))
    for xmlid, names in STAGE_MAPPING.items():
        stage_id = stage_ids.get(xmlid)
        if stage_id:
            cr.execute(
                "UPDATE crm_stage SET name = %s WHERE id = %s",
                (json.dumps({"en_US": names["name_en"], "ru_RU": names["name_ru"]}), stage_id),
            )
            _logger.info("Migration 19.0.1.7.2: renamed stage %s to %s", xmlid, names["name_ru"])

    estate_ids = _resolve_xmlids(cr, list(ESTATE_STAGES.keys()))
    for xmlid, data in ESTATE_STAGES.items():
        stage_id = estate_ids.get(xmlid)
        if stage_id:
            cr.execute(
                "UPDATE crm_stage SET name = %s, sequence = %s WHERE id = %s",
                (json.dumps({"en_US": data["name_en"], "ru_RU": data["name_ru"]}), data["sequence"], stage_id),
            )
            _logger.info(
                "Migration 19.0.1.7.2: renamed stage %s to %s (seq %s)", xmlid, data["name_ru"], data["sequence"]
            )

    cr.execute(
        """
        SELECT s.id FROM crm_stage s
        JOIN ir_model_data m ON m.res_id = s.id AND m.model = 'crm.stage'
        WHERE m.module = 'estate_kit' AND m.name = 'crm_stage_lost'
        """
    )
    if not cr.fetchone():
        lost_name = json.dumps({"en_US": "Lost", "ru_RU": "Потеряно"})
        cr.execute(
            """
            INSERT INTO crm_stage (name, sequence, is_won, fold, create_uid, write_uid)
            VALUES (%s, 80, false, true, 1, 1)
            RETURNING id
            """,
            (lost_name,),
        )
        lost_id = cr.fetchone()[0]
        cr.execute(
            """
            INSERT INTO ir_model_data (module, name, model, res_id)
            VALUES ('estate_kit', 'crm_stage_lost', 'crm.stage', %s)
            """,
            (lost_id,),
        )
        _logger.info("Migration 19.0.1.7.2: created Lost stage")

    proposition_id = stage_ids.get("crm.stage_lead3")
    if proposition_id:
        cr.execute(
            "UPDATE crm_stage SET sequence = 6 WHERE id = %s",
            (proposition_id,),
        )
        _logger.info("Migration 19.0.1.7.2: updated Proposition sequence to 6")

    won_id = stage_ids.get("crm.stage_lead4")
    if won_id:
        cr.execute("UPDATE crm_stage SET sequence = 70 WHERE id = %s", (won_id,))

    _logger.info("Migration 19.0.1.7.2: CRM stages normalized successfully")


def _resolve_xmlids(cr, xmlids):
    resolved = {}
    for xmlid in xmlids:
        module, name = xmlid.split(".", 1)
        cr.execute(
            "SELECT res_id FROM ir_model_data WHERE module = %s AND name = %s AND model = 'crm.stage'",
            (module, name),
        )
        row = cr.fetchone()
        if row:
            resolved[xmlid] = row[0]
    return resolved
