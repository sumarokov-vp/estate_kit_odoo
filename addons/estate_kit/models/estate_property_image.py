import base64
import logging

import requests

from odoo import api, fields, models

from ..services.api_client import EstateKitApiClient

_logger = logging.getLogger(__name__)

IMAGE_DOWNLOAD_TIMEOUT = 30


class EstatePropertyImage(models.Model):
    _name = "estate.property.image"
    _description = "Property Image"
    _order = "sequence, id"

    property_id = fields.Many2one(
        "estate.property",
        required=True,
        ondelete="cascade",
        index=True,
    )
    name = fields.Char()
    image = fields.Binary(attachment=True)
    sequence = fields.Integer(default=10)
    is_main = fields.Boolean(
        string="Main Image",
        help="This image will be used as the property thumbnail",
    )
    external_id = fields.Integer("API Image ID", index=True, copy=False)
    image_url = fields.Char("S3 URL", copy=False)

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        if not self.env.context.get("skip_api_sync"):
            for record in records:
                record._push_image_to_api()
        return records

    def unlink(self):
        images_to_delete = [
            (rec.external_id, rec.property_id.external_id)
            for rec in self
            if rec.external_id and not self.env.context.get("skip_api_sync")
        ]
        result = super().unlink()
        if images_to_delete:
            client = EstateKitApiClient(self.env)
            if client._is_configured:
                for image_external_id, _property_external_id in images_to_delete:
                    response = client.delete(f"/property-images/{image_external_id}")
                    if response is not None:
                        _logger.info(
                            "Deleted image %d from API", image_external_id
                        )
                    else:
                        _logger.warning(
                            "Failed to delete image %d from API", image_external_id
                        )
        return result

    def _push_image_to_api(self):
        self.ensure_one()
        if not self.image or not self.property_id.external_id:
            return

        client = EstateKitApiClient(self.env)
        if not client._is_configured:
            return

        file_data = base64.b64decode(self.image)
        file_name = self.name or f"image_{self.id}.jpg"

        response = client.upload(
            "/property-images/upload",
            file_field="file",
            file_name=file_name,
            file_data=file_data,
            extra_data={"property_id": str(self.property_id.external_id)},
        )

        if response:
            vals = {}
            if response.get("id"):
                vals["external_id"] = response["id"]
            if response.get("url"):
                vals["image_url"] = response["url"]
            if vals:
                self.with_context(skip_api_sync=True).write(vals)
                _logger.info(
                    "Pushed image %d to API (external_id=%s)",
                    self.id,
                    response.get("id"),
                )
        else:
            _logger.warning("Failed to push image %d to API", self.id)

    @api.model
    def _pull_images_for_property(self, property_record):
        if not property_record.external_id:
            return

        client = EstateKitApiClient(self.env)
        if not client._is_configured:
            return

        response = client.get(
            "/property-images",
            params={"property_id": property_record.external_id},
        )
        if not response:
            return

        items = response.get("items", [])
        if not items:
            return

        existing_images = self.search([
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

            self.with_context(skip_api_sync=True).create({
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

    @api.model
    def _download_image(self, url):
        if not url:
            return False
        response = requests.get(url, timeout=IMAGE_DOWNLOAD_TIMEOUT)
        if response.status_code == 200 and response.content:
            return base64.b64encode(response.content).decode("ascii")
        _logger.warning("Failed to download image from %s (status=%d)", url, response.status_code)
        return False
