import logging

_logger = logging.getLogger(__name__)

QUALIFIED_XMLID = ("crm", "stage_lead2")
NEW_STAGE_XMLID = ("crm", "stage_lead1")


def migrate(cr, version):
    if not version:
        return

    _logger.info("Migration 19.0.1.7.3: archive Qualified stage")

    # Find Qualified stage
    cr.execute(
        "SELECT res_id FROM ir_model_data WHERE module = %s AND name = %s AND model = 'crm.stage'",
        QUALIFIED_XMLID,
    )
    row = cr.fetchone()
    if not row:
        _logger.info("Qualified stage not found, skipping")
        return

    qualified_id = row[0]

    # Find New stage to reassign leads
    cr.execute(
        "SELECT res_id FROM ir_model_data WHERE module = %s AND name = %s AND model = 'crm.stage'",
        NEW_STAGE_XMLID,
    )
    row = cr.fetchone()
    if row:
        new_id = row[0]
        cr.execute(
            "UPDATE crm_lead SET stage_id = %s WHERE stage_id = %s",
            (new_id, qualified_id),
        )
        moved = cr.rowcount
        if moved:
            _logger.info("Moved %d leads from Qualified to New", moved)

    # Delete the stage and its xmlid reference
    cr.execute(
        "DELETE FROM ir_model_data WHERE module = %s AND name = %s AND model = 'crm.stage'",
        QUALIFIED_XMLID,
    )
    cr.execute("DELETE FROM crm_stage WHERE id = %s", (qualified_id,))
    _logger.info("Deleted Qualified stage (id=%s)", qualified_id)
