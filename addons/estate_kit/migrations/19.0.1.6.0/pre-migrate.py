"""Pre-migration: extract image_key/thumbnail_key from stored URLs before columns are dropped.

image_url and thumbnail_url become non-stored computed fields in this version,
so Odoo will drop those columns during the upgrade. We must extract keys from
the existing URLs into image_key/thumbnail_key BEFORE that happens.

URL format: https://domain.com/<key>
  - image_url:     https://cdn.example.com/a1b2c3d4.jpg       -> key = a1b2c3d4.jpg
  - thumbnail_url: https://cdn.example.com/thumbs/a1b2c3d4.jpg -> key = thumbs/a1b2c3d4.jpg
"""

import logging

_logger = logging.getLogger(__name__)


def _extract_key(url):
    """Extract object key from a full S3/CDN URL."""
    if not url:
        return None
    parts = url.split("/", 3)
    if len(parts) >= 4 and parts[3]:
        return parts[3]
    return None


def migrate(cr, version):
    if not version:
        return

    # Check if image_url column still exists (it should at pre-migrate stage)
    cr.execute("""
        SELECT column_name
        FROM information_schema.columns
        WHERE table_name = 'estate_property_image'
          AND column_name IN ('image_url', 'thumbnail_url')
    """)
    existing_cols = {row[0] for row in cr.fetchall()}

    if "image_url" not in existing_cols:
        _logger.info("Migration 19.0.1.6.0: image_url column not found, skipping")
        return

    # Backfill image_key from image_url where image_key is NULL
    cr.execute("""
        SELECT id, image_url, thumbnail_url
        FROM estate_property_image
        WHERE (image_key IS NULL OR image_key = '')
          AND image_url IS NOT NULL
          AND image_url != ''
    """)
    rows = cr.fetchall()

    updated = 0
    for record_id, image_url, thumbnail_url in rows:
        image_key = _extract_key(image_url)
        thumbnail_key = _extract_key(thumbnail_url) if thumbnail_url else None

        if image_key:
            cr.execute("""
                UPDATE estate_property_image
                SET image_key = %s,
                    thumbnail_key = COALESCE(%s, thumbnail_key)
                WHERE id = %s
            """, (image_key, thumbnail_key, record_id))
            updated += 1

    _logger.info(
        "Migration 19.0.1.6.0: backfilled image_key for %d records from image_url",
        updated,
    )
