import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    if not version:
        return

    # Add new columns for Image Service keys/URLs
    cr.execute("""
        ALTER TABLE estate_property_image
        ADD COLUMN IF NOT EXISTS image_key VARCHAR,
        ADD COLUMN IF NOT EXISTS thumbnail_key VARCHAR,
        ADD COLUMN IF NOT EXISTS thumbnail_url VARCHAR
    """)

    # Drop old binary attachment records (image and thumbnail fields)
    cr.execute("""
        DELETE FROM ir_attachment
        WHERE res_model = 'estate.property.image'
        AND res_field IN ('image', 'thumbnail')
    """)
    deleted = cr.rowcount
    _logger.info(
        "Migration 19.0.1.5.0: added image_key/thumbnail_key/thumbnail_url columns, "
        "deleted %d binary attachment records", deleted
    )
