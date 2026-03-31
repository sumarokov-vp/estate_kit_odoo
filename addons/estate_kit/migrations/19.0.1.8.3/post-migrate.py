import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    if not version:
        return

    # Delete "Просмотр" stage
    cr.execute(
        "SELECT res_id FROM ir_model_data "
        "WHERE module = %s AND name = %s AND model = 'crm.stage'",
        ("estate_kit", "crm_stage_viewing"),
    )
    row = cr.fetchone()
    if not row:
        return

    stage_id = row[0]

    # Move leads from "Просмотр" to "Подобрано"
    cr.execute(
        "SELECT res_id FROM ir_model_data "
        "WHERE module = %s AND name = %s AND model = 'crm.stage'",
        ("estate_kit", "crm_stage_matched"),
    )
    target_id = cr.fetchone()[0]
    cr.execute(
        "UPDATE crm_lead SET stage_id = %s WHERE stage_id = %s",
        (target_id, stage_id),
    )

    # Update existing match states: interested → selected, viewed stays
    cr.execute(
        "UPDATE estate_lead_match SET state = 'selected' WHERE state = 'interested'"
    )

    # Delete stage
    cr.execute(
        "DELETE FROM ir_model_data WHERE res_id = %s AND model = 'crm.stage'",
        (stage_id,),
    )
    cr.execute("DELETE FROM crm_stage WHERE id = %s", (stage_id,))
    _logger.info("Deleted CRM stage 'Просмотр' (id=%s)", stage_id)
