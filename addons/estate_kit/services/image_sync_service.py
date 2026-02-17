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

    def push_image(self, image_record):
        if not image_record.image or not image_record.property_id.external_id:
            return
        if not self.client.is_configured:
            return

        file_data = base64.b64decode(image_record.image)
        file_name = image_record.name or f"image_{image_record.id}.jpg"

        response = self.client.upload(
            "/property-images/upload",
            file_field="file",
            file_name=file_name,
            file_data=file_data,
            extra_data={"property_id": str(image_record.property_id.external_id)},
        )

        if response:
            vals = {}
            if response.get("id"):
                vals["external_id"] = response["id"]
            if response.get("url"):
                vals["image_url"] = response["url"]
            if vals:
                image_record.with_context(skip_api_sync=True).write(vals)
                _logger.info(
                    "Pushed image %d to API (external_id=%s)",
                    image_record.id,
                    response.get("id"),
                )
        else:
            _logger.warning("Failed to push image %d to API", image_record.id)

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

            image_binary = self._download_image(image_url) if image_url else False

            ImageModel.with_context(skip_api_sync=True).create({
                "property_id": property_record.id,
                "name": item.get("name", ""),
                "image": image_binary,
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
    def _download_image(url):
        if not url:
            return False
        response = requests.get(url, timeout=IMAGE_DOWNLOAD_TIMEOUT)
        if response.status_code == 200 and response.content:
            return base64.b64encode(response.content).decode("ascii")
        _logger.warning("Failed to download image from %s (status=%d)", url, response.status_code)
        return False
