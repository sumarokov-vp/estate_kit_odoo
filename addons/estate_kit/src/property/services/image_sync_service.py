import logging

from ...shared.services.api_client import EstateKitApiClient

_logger = logging.getLogger(__name__)


class ImageSyncService:
    def __init__(self, env):
        self.env = env
        self.client = EstateKitApiClient(env)

    def push_images_for_property(self, property_record):
        """Push image URLs to the central MLS API for a property."""
        if not property_record.external_id:
            return
        if not self.client.is_configured:
            return

        images_without_external = self.env["estate.property.image"].search([
            ("property_id", "=", property_record.id),
            ("image_key", "!=", False),
            "|",
            ("external_id", "=", False),
            ("external_id", "=", 0),
        ])

        for img in images_without_external:
            response = self.client.post(
                "/property-images",
                data={
                    "property_id": property_record.external_id,
                    "image_key": img.image_key,
                    "thumbnail_key": img.thumbnail_key or "",
                    "name": img.name or "",
                    "sequence": img.sequence,
                    "is_main": img.is_main,
                },
            )
            if response:
                img.with_context(skip_api_sync=True).write({
                    "external_id": response.get("id"),
                })
                _logger.info(
                    "Pushed image URL to API (external_id=%s)", response.get("id"),
                )
            else:
                _logger.warning("Failed to push image URL to API")

    def delete_images(self, images_to_delete):
        """Delete images from the central MLS API."""
        if not images_to_delete or not self.client.is_configured:
            return
        for image_external_id, _property_external_id in images_to_delete:
            response = self.client.delete(f"/property-images/{image_external_id}")
            if response is not None:
                _logger.info("Deleted image %d from API", image_external_id)
            else:
                _logger.warning("Failed to delete image %d from API", image_external_id)

    @staticmethod
    def _extract_key_from_url(url):
        """Extract the object key from a full CDN/S3 URL.

        Example: 'https://cdn.example.com/a1b2c3.jpg' -> 'a1b2c3.jpg'
                 'https://cdn.example.com/thumbs/a1b2c3.jpg' -> 'thumbs/a1b2c3.jpg'
        """
        if not url:
            return ""
        # Remove protocol + domain: everything after the third slash
        parts = url.split("/", 3)
        if len(parts) >= 4:
            return parts[3]
        return ""

    def pull_images_for_property(self, property_record):
        """Pull images from the central MLS API and create local records."""
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

            image_key = self._extract_key_from_url(item.get("url", ""))
            thumbnail_key = self._extract_key_from_url(item.get("thumbnail_url", ""))

            if api_image_id in existing_map:
                existing_img = existing_map[api_image_id]
                update_vals = {}
                if existing_img.image_key != image_key and image_key:
                    update_vals["image_key"] = image_key
                if existing_img.thumbnail_key != thumbnail_key and thumbnail_key:
                    update_vals["thumbnail_key"] = thumbnail_key
                if update_vals:
                    existing_img.with_context(skip_api_sync=True).write(update_vals)
                continue

            ImageModel.with_context(skip_api_sync=True).create({
                "property_id": property_record.id,
                "name": item.get("name", ""),
                "image_key": image_key,
                "thumbnail_key": thumbnail_key,
                "external_id": api_image_id,
                "sequence": item.get("sequence", 10),
                "is_main": item.get("is_main", False),
            })

        _logger.info(
            "Pulled %d images for property %d (external_id=%d)",
            len(items),
            property_record.id,
            property_record.external_id,
        )
