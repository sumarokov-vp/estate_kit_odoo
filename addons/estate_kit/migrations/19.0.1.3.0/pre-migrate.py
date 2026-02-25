import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    if not version:
        return

    # Rename column image -> thumbnail in the database
    cr.execute("""
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'estate_property_image'
                AND column_name = 'image'
            ) THEN
                ALTER TABLE estate_property_image
                RENAME COLUMN image TO thumbnail;
            END IF;
        END $$;
    """)

    _logger.info("Renamed estate_property_image.image -> thumbnail")
