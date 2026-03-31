import logging

_logger = logging.getLogger(__name__)

STATE_TO_XMLID = {
    "new": "match_stage_new",
    "viewed": "match_stage_viewed",
    "rejected": "match_stage_rejected",
    "selected": "match_stage_selected",
    "interested": "match_stage_selected",
}


def migrate(cr, version):
    if not version:
        return

    # Check if old state column exists
    cr.execute(
        "SELECT column_name FROM information_schema.columns "
        "WHERE table_name = 'estate_lead_match' AND column_name = 'state'"
    )
    if not cr.fetchone():
        return

    # Map old state values to new stage_id
    for state, xmlid in STATE_TO_XMLID.items():
        cr.execute(
            "SELECT res_id FROM ir_model_data "
            "WHERE module = 'estate_kit' AND name = %s "
            "AND model = 'estate.lead.match.stage'",
            (xmlid,),
        )
        row = cr.fetchone()
        if not row:
            continue
        stage_id = row[0]
        cr.execute(
            "UPDATE estate_lead_match SET stage_id = %s WHERE state = %s",
            (stage_id, state),
        )
        updated = cr.rowcount
        if updated:
            _logger.info("Migrated %d matches state=%s -> stage_id=%s", updated, state, stage_id)

    # Set default stage for any remaining nulls
    cr.execute(
        "SELECT res_id FROM ir_model_data "
        "WHERE module = 'estate_kit' AND name = 'match_stage_new' "
        "AND model = 'estate.lead.match.stage'"
    )
    row = cr.fetchone()
    if row:
        cr.execute(
            "UPDATE estate_lead_match SET stage_id = %s WHERE stage_id IS NULL",
            (row[0],),
        )
