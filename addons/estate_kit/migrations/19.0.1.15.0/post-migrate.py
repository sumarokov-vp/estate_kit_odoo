import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    if not version:
        return

    cr.execute(
        "SELECT column_name FROM information_schema.columns "
        "WHERE table_name = 'estate_property' AND column_name = 'residential_complex'"
    )
    if not cr.fetchone():
        _logger.info("Column residential_complex already removed, skipping migration")
        return

    cr.execute(
        "SELECT id, residential_complex, city_id FROM estate_property "
        "WHERE residential_complex IS NOT NULL AND residential_complex != ''"
    )
    rows = cr.fetchall()
    _logger.info("Migrating residential_complex for %d properties", len(rows))

    for property_id, complex_name, city_id in rows:
        complex_name = complex_name.strip()
        if not complex_name:
            continue

        if city_id:
            cr.execute(
                "SELECT id FROM estate_residential_complex "
                "WHERE LOWER(name) = LOWER(%s) AND city_id = %s LIMIT 1",
                (complex_name, city_id),
            )
        else:
            cr.execute(
                "SELECT id FROM estate_residential_complex "
                "WHERE LOWER(name) = LOWER(%s) AND city_id IS NULL LIMIT 1",
                (complex_name,),
            )
        found = cr.fetchone()

        if found:
            complex_id = found[0]
        else:
            cr.execute(
                "INSERT INTO estate_residential_complex "
                "(name, city_id, sequence, active, create_date, write_date) "
                "VALUES (%s, %s, 10, TRUE, NOW(), NOW()) RETURNING id",
                (complex_name, city_id),
            )
            complex_id = cr.fetchone()[0]
            _logger.info("Created ЖК '%s' (id=%s, city_id=%s)", complex_name, complex_id, city_id)

        cr.execute(
            "UPDATE estate_property SET residential_complex_id = %s WHERE id = %s",
            (complex_id, property_id),
        )

    cr.execute("ALTER TABLE estate_property DROP COLUMN residential_complex")
    _logger.info("Dropped old column estate_property.residential_complex")
