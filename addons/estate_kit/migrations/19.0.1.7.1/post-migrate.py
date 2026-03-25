import logging

_logger = logging.getLogger(__name__)

EXPECTED_IMPLIED_XMLIDS = {
    "estate_kit.group_estate_isa": [
        "sales_team.group_sale_salesman",
    ],
    "estate_kit.group_estate_buyer_agent": [
        "estate_kit.group_estate_isa",
        "sales_team.group_sale_salesman_all_leads",
    ],
    "estate_kit.group_estate_transaction_coordinator": [
        "estate_kit.group_estate_buyer_agent",
    ],
    "estate_kit.group_estate_listing_agent": [],
    "estate_kit.group_estate_listing_coordinator": [
        "estate_kit.group_estate_listing_agent",
    ],
    "estate_kit.group_estate_team_lead": [
        "estate_kit.group_estate_listing_coordinator",
        "estate_kit.group_estate_transaction_coordinator",
    ],
    "estate_kit.group_estate_marketing_viewer": [],
    "estate_kit.group_estate_marketing": [
        "estate_kit.group_estate_marketing_viewer",
    ],
    "estate_kit.group_estate_marketing_lead": [
        "estate_kit.group_estate_marketing",
    ],
}


def migrate(cr, version):
    if not version:
        return

    group_ids = _resolve_xmlids(cr, EXPECTED_IMPLIED_XMLIDS)
    if not group_ids:
        _logger.warning("Migration 19.0.1.7.1: no estate groups resolved, skipping")
        return

    restored_groups = 0

    for group_xmlid, implied_xmlids in EXPECTED_IMPLIED_XMLIDS.items():
        group_id = group_ids.get(group_xmlid)
        if not group_id:
            continue

        implied_ids = [group_ids[xmlid] for xmlid in implied_xmlids if group_ids.get(xmlid)]

        cr.execute("DELETE FROM res_groups_implied_rel WHERE gid = %s", (group_id,))

        for implied_id in implied_ids:
            cr.execute(
                """
                INSERT INTO res_groups_implied_rel (gid, hid)
                VALUES (%s, %s)
                ON CONFLICT DO NOTHING
                """,
                (group_id, implied_id),
            )

        restored_groups += 1

    _logger.info(
        "Migration 19.0.1.7.1: normalized implied_ids for %d Estate Kit groups",
        restored_groups,
    )


def _resolve_xmlids(cr, groups_map):
    xmlids = set(groups_map)
    for implied_xmlids in groups_map.values():
        xmlids.update(implied_xmlids)

    resolved = {}
    for xmlid in xmlids:
        module, name = xmlid.split(".", 1)
        cr.execute(
            """
            SELECT res_id
            FROM ir_model_data
            WHERE module = %s AND name = %s AND model = 'res.groups'
            """,
            (module, name),
        )
        row = cr.fetchone()
        if not row:
            _logger.warning("Migration 19.0.1.7.1: xmlid %s not found", xmlid)
            continue
        resolved[xmlid] = row[0]

    return resolved
