import base64
import logging

import requests

from .api_client import EstateKitApiClient

_logger = logging.getLogger(__name__)

IMAGE_DOWNLOAD_TIMEOUT = 30


class ImageSyncService:
    def __init__(self, env):
        self.env = env
        self.client = EstateKitApiClient(env)

    def push_image_binary(self, image_b64, file_name, property_external_id):
        """Upload full-size image binary to API. Returns {id, url} or None."""
        if not image_b64 or not property_external_id:
            return None
        if not self.client.is_configured:
            return None

        file_data = base64.b64decode(image_b64)
        if not file_name.endswith((".jpg", ".jpeg", ".png", ".webp")):
            file_name = f"{file_name}.jpg"

        response = self.client.upload(
            "/property-images/upload",
            file_field="file",
            file_name=file_name,
            file_data=file_data,
            extra_data={"property_id": str(property_external_id)},
        )

        if response:
            _logger.info(
                "Pushed image to API (external_id=%s, url=%s)",
                response.get("id"),
                response.get("url"),
            )
            return response

        _logger.warning("Failed to push image to API")
        return None

    def delete_images(self, images_to_delete):
        if not images_to_delete or not self.client.is_configured:
            return
        for image_external_id, _property_external_id in images_to_delete:
            response = self.client.delete(f"/property-images/{image_external_id}")
            if response is not None:
                _logger.info("Deleted image %d from API", image_external_id)
            else:
                _logger.warning("Failed to delete image %d from API", image_external_id)

    def pull_images_for_property(self, property_record):
        if not property_record.external_id:
            return
        if not self.client.is_configured:
            return

        response = self.client.get(
            "/property-images",
            params={"property_id": property_record.external_id},
        )
        if not response:
            return

        items = response.get("items", [])
        if not items:
            return

        ImageModel = self.env["estate.property.image"]
        existing_images = ImageModel.search([
            ("property_id", "=", property_record.id),
            ("external_id", "!=", False),
            ("external_id", "!=", 0),
        ])
        existing_map = {img.external_id: img for img in existing_images}

        for item in items:
            api_image_id = item.get("id")
            if not api_image_id:
                continue

            image_url = item.get("url", "")

            if api_image_id in existing_map:
                existing_img = existing_map[api_image_id]
                if existing_img.image_url != image_url and image_url:
                    existing_img.with_context(skip_api_sync=True).write(
                        {"image_url": image_url}
                    )
                continue

            # Download and create thumbnail only (no full-size binary stored)
            thumbnail_b64 = self._download_and_thumbnail(image_url) if image_url else False

            ImageModel.with_context(skip_api_sync=True).create({
                "property_id": property_record.id,
                "name": item.get("name", ""),
                "thumbnail": thumbnail_b64,
                "external_id": api_image_id,
                "image_url": image_url,
                "sequence": item.get("sequence", 10),
                "is_main": item.get("is_main", False),
            })

        _logger.info(
            "Pulled %d images for property %d (external_id=%d)",
            len(items),
            property_record.id,
            property_record.external_id,
        )

    @staticmethod
    def _download_and_thumbnail(url):
        """Download image from URL and return base64-encoded 256x256 thumbnail."""
        if not url:
            return False
        try:
            response = requests.get(url, timeout=IMAGE_DOWNLOAD_TIMEOUT)
        except requests.RequestException:
            _logger.warning("Failed to download image from %s", url)
            return False

        if response.status_code != 200 or not response.content:
            _logger.warning("Failed to download image from %s (status=%d)", url, response.status_code)
            return False

        try:
            from ..models.estate_property_image import _make_thumbnail
            raw_b64 = base64.b64encode(response.content).decode("ascii")
            return _make_thumbnail(raw_b64)
        except Exception:
            _logger.warning("Failed to create thumbnail from %s, storing full image", url)
            return base64.b64encode(response.content).decode("ascii")
