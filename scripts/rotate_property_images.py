#!/usr/bin/env python3
"""
Rotate existing property images in the image service.

Usage:
    python rotate_property_images.py <property_id> [property_id ...] [--degrees 90]

Example:
    python rotate_property_images.py 73
    python rotate_property_images.py 73 81 --degrees 90
"""

import argparse
import io
import logging
import os
import sys

import grpc
import psycopg2
from PIL import Image

sys.path.insert(0, "/mnt/extra-addons/estate_kit/src/shared/services")
from generated import image_service_pb2, image_service_pb2_grpc

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
_logger = logging.getLogger(__name__)

IMAGE_SERVICE_ADDRESS = os.getenv("IMAGE_SERVICE_ADDRESS", "image-service:50051")
GRPC_TIMEOUT = 60

DB_HOST = os.getenv("DB_HOST", "db")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "royal_estate")
DB_USER = os.getenv("DB_USER", "odoo")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")


def get_db_connection():
    return psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
    )


def download_image(stub, key: str) -> tuple[bytes, str] | None:
    try:
        response = stub.GetImage(
            image_service_pb2.GetImageRequest(key=key),
            timeout=GRPC_TIMEOUT,
        )
        return response.data, response.content_type
    except grpc.RpcError as e:
        _logger.error("Download failed for key %s: %s", key, e)
        return None


def upload_image(stub, data: bytes, content_type: str) -> dict | None:
    try:
        response = stub.UploadImage(
            image_service_pb2.UploadImageRequest(
                data=data,
                content_type=content_type,
                generate_thumbnail=True,
            ),
            timeout=GRPC_TIMEOUT,
        )
        return {"key": response.key, "thumbnail_key": response.thumbnail_key}
    except grpc.RpcError as e:
        _logger.error("Upload failed: %s", e)
        return None


def delete_images(stub, keys: list[str]):
    keys = [k for k in keys if k]
    if not keys:
        return
    try:
        stub.DeleteImages(
            image_service_pb2.DeleteImagesRequest(keys=keys),
            timeout=GRPC_TIMEOUT,
        )
    except grpc.RpcError as e:
        _logger.warning("Delete failed for keys %s: %s", keys, e)


def rotate_image(data: bytes, degrees: int) -> tuple[bytes, str]:
    image = Image.open(io.BytesIO(data))
    # PIL rotate is CCW, so for CW rotation negate degrees
    rotated = image.rotate(-degrees, expand=True)
    buf = io.BytesIO()
    fmt = image.format or "JPEG"
    if fmt == "JPEG":
        rotated.save(buf, format="JPEG", quality=85, optimize=True)
    else:
        rotated.save(buf, format=fmt)
    return buf.getvalue(), "image/jpeg" if fmt == "JPEG" else f"image/{fmt.lower()}"


def process_property(conn, stub, property_id: int, degrees: int, dry_run: bool, name_prefix: str | None = None):
    cur = conn.cursor()
    if name_prefix:
        cur.execute(
            "SELECT id, image_key, thumbnail_key, name FROM estate_property_image "
            "WHERE property_id = %s AND image_key IS NOT NULL AND name ILIKE %s ORDER BY sequence, id",
            (property_id, name_prefix + "%"),
        )
    else:
        cur.execute(
            "SELECT id, image_key, thumbnail_key, name FROM estate_property_image "
            "WHERE property_id = %s AND image_key IS NOT NULL ORDER BY sequence, id",
            (property_id,),
        )
    rows = cur.fetchall()
    if not rows:
        _logger.warning("No images found for property %d (filter: %s)", property_id, name_prefix or "none")
        return

    _logger.info("Property %d: found %d image(s) (filter: %s)", property_id, len(rows), name_prefix or "none")

    for img_id, image_key, thumbnail_key, name in rows:
        _logger.info("  [%d] %s — key: %s", img_id, name or "", image_key)

        result = download_image(stub, image_key)
        if not result:
            _logger.error("  Skipping — download failed")
            continue
        data, content_type = result

        rotated_data, rotated_content_type = rotate_image(data, degrees)
        _logger.info("  Rotated %d° CW (%d bytes → %d bytes)", degrees, len(data), len(rotated_data))

        if dry_run:
            _logger.info("  [dry-run] Would re-upload and update DB record %d", img_id)
            continue

        new_keys = upload_image(stub, rotated_data, rotated_content_type)
        if not new_keys:
            _logger.error("  Skipping — upload failed")
            continue

        _logger.info("  Uploaded: new_key=%s", new_keys["key"])

        cur.execute(
            "UPDATE estate_property_image SET image_key = %s, thumbnail_key = %s WHERE id = %s",
            (new_keys["key"], new_keys["thumbnail_key"], img_id),
        )
        conn.commit()

        delete_images(stub, [image_key, thumbnail_key])
        _logger.info("  Deleted old keys")

    cur.close()


def main():
    parser = argparse.ArgumentParser(description="Rotate property images in image service")
    parser.add_argument("property_ids", type=int, nargs="+", help="Property IDs to process")
    parser.add_argument("--degrees", type=int, default=90, help="Degrees to rotate clockwise (default: 90)")
    parser.add_argument("--dry-run", action="store_true", help="Preview without making changes")
    parser.add_argument(
        "--name-prefix",
        type=str,
        default=None,
        help="Only rotate images whose name starts with this prefix (e.g. IMG_)",
    )
    args = parser.parse_args()

    if args.dry_run:
        _logger.info("=== DRY RUN — no changes will be made ===")

    conn = get_db_connection()
    channel = grpc.insecure_channel(IMAGE_SERVICE_ADDRESS)
    stub = image_service_pb2_grpc.ImageServiceStub(channel)

    try:
        for pid in args.property_ids:
            process_property(conn, stub, pid, args.degrees, args.dry_run, args.name_prefix)
    finally:
        conn.close()
        channel.close()

    _logger.info("Done.")


if __name__ == "__main__":
    main()
