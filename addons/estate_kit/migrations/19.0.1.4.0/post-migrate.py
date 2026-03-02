import base64
import logging

import requests

_logger = logging.getLogger(__name__)

REQUEST_TIMEOUT = 30


def migrate(cr, version):
    if not version:
        return

    # Find all estate.property.image records with their image_url
    cr.execute("""
        SELECT id, image_url
        FROM estate_property_image
    """)
    records = cr.fetchall()

    if not records:
        _logger.info("No estate.property.image records found, skipping")
        return

    restored = 0
    copied = 0

    for record_id, image_url in records:
        # Check if image attachment already exists
        cr.execute("""
            SELECT id FROM ir_attachment
            WHERE res_model = 'estate.property.image'
            AND res_id = %s
            AND res_field = 'image'
        """, (record_id,))
        if cr.fetchone():
            continue

        if image_url:
            # Download original from S3
            image_data = _download_image(image_url)
            if image_data:
                _create_attachment(cr, record_id, 'image', image_data)
                restored += 1
                continue

        # Fallback: copy thumbnail to image
        cr.execute("""
            SELECT db_datas, store_fname, mimetype, file_size
            FROM ir_attachment
            WHERE res_model = 'estate.property.image'
            AND res_id = %s
            AND res_field = 'thumbnail'
        """, (record_id,))
        thumb = cr.fetchone()
        if thumb and thumb[0]:
            _create_attachment(cr, record_id, 'image', thumb[0],
                               mimetype=thumb[2], file_size=thumb[3])
            copied += 1

    _logger.info(
        "Migration 19.0.1.4.0: restored %d images from S3, "
        "copied %d from thumbnail", restored, copied
    )


def _download_image(url):
    try:
        resp = requests.get(url, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        return base64.b64encode(resp.content).decode('ascii')
    except Exception:
        _logger.warning("Failed to download image from %s", url, exc_info=True)
        return None


def _create_attachment(cr, res_id, res_field, db_datas, mimetype=None, file_size=None):
    if file_size is None:
        file_size = len(base64.b64decode(db_datas))
    if mimetype is None:
        mimetype = 'image/jpeg'

    cr.execute("""
        INSERT INTO ir_attachment
            (name, res_model, res_id, res_field, type, db_datas, mimetype,
             file_size, create_uid, write_uid, create_date, write_date)
        VALUES
            (%s, 'estate.property.image', %s, %s, 'binary', %s, %s,
             %s, 1, 1, NOW() AT TIME ZONE 'UTC', NOW() AT TIME ZONE 'UTC')
    """, (res_field, res_id, res_field, db_datas, mimetype, file_size))
