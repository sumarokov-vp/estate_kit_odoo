import base64
import io
import logging

_logger = logging.getLogger(__name__)

THUMBNAIL_SIZE = (256, 256)


def migrate(cr, version):
    if not version:
        return

    # Since images are stored as attachments (ir.attachment), we need to
    # resize them via the ORM. But in migration scripts we use raw SQL
    # for the attachment table.

    # Find all attachments for estate.property.image thumbnail field
    cr.execute("""
        SELECT id, db_datas, store_fname
        FROM ir_attachment
        WHERE res_model = 'estate.property.image'
        AND res_field = 'thumbnail'
        AND db_datas IS NOT NULL
    """)
    rows = cr.fetchall()

    if not rows:
        # Try old field name
        cr.execute("""
            SELECT id, db_datas, store_fname
            FROM ir_attachment
            WHERE res_model = 'estate.property.image'
            AND res_field = 'image'
            AND db_datas IS NOT NULL
        """)
        rows = cr.fetchall()

        # Update res_field from 'image' to 'thumbnail'
        if rows:
            cr.execute("""
                UPDATE ir_attachment
                SET res_field = 'thumbnail'
                WHERE res_model = 'estate.property.image'
                AND res_field = 'image'
            """)

    try:
        from PIL import Image
    except ImportError:
        _logger.warning("Pillow not installed, skipping thumbnail resize migration")
        return

    resized = 0
    for att_id, db_datas, store_fname in rows:
        if not db_datas:
            continue
        try:
            raw = base64.b64decode(db_datas)
            img = Image.open(io.BytesIO(raw))

            # Skip if already small enough
            if img.width <= THUMBNAIL_SIZE[0] and img.height <= THUMBNAIL_SIZE[1]:
                continue

            img.thumbnail(THUMBNAIL_SIZE, Image.LANCZOS)
            buf = io.BytesIO()
            fmt = img.format or "JPEG"
            if fmt.upper() == "JPEG":
                img = img.convert("RGB")
            img.save(buf, format=fmt, quality=85)
            new_b64 = base64.b64encode(buf.getvalue())

            cr.execute(
                "UPDATE ir_attachment SET db_datas = %s, file_size = %s WHERE id = %s",
                (new_b64.decode("ascii"), len(buf.getvalue()), att_id),
            )
            resized += 1
        except Exception:
            _logger.warning("Failed to resize attachment %d", att_id, exc_info=True)

    _logger.info("Resized %d image attachments to thumbnails", resized)
