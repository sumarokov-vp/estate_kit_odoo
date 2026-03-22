import base64
import logging
import mimetypes

from odoo import api, fields, models

from ..services.image_service import Factory as ImageServiceFactory
from ..services.image_sync_service import ImageSyncService

_logger = logging.getLogger(__name__)


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
    image_key = fields.Char("Image Key", copy=False)
    thumbnail_key = fields.Char("Thumbnail Key", copy=False)
    sequence = fields.Integer(default=10)
    is_main = fields.Boolean(
        string="Main Image",
        help="This image will be used as the property thumbnail",
    )
    external_id = fields.Integer("API Image ID", index=True, copy=False)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            image_b64 = vals.pop("image", None)
            if image_b64 and not vals.get("image_key"):
                self._upload_to_image_service(vals, image_b64)
        return super().create(vals_list)

    def unlink(self):
        skip_sync = self.env.context.get("skip_api_sync")
        keys_to_delete = []
        api_images_to_delete = []
        for rec in self:
            if not skip_sync:
                if rec.image_key:
                    keys_to_delete.append(rec.image_key)
                if rec.thumbnail_key:
                    keys_to_delete.append(rec.thumbnail_key)
                if rec.external_id:
                    api_images_to_delete.append(
                        (rec.external_id, rec.property_id.external_id)
                    )
        result = super().unlink()
        if keys_to_delete:
            ImageServiceFactory.create(self.env).delete_many(keys_to_delete)
        if api_images_to_delete:
            ImageSyncService(self.env).delete_images(api_images_to_delete)
        return result

    def _upload_to_image_service(self, vals, image_b64):
        """Upload image binary to Image Service via gRPC, populate vals with keys."""
        try:
            file_data = base64.b64decode(image_b64)
        except Exception:
            _logger.warning("Failed to decode base64 image data")
            return

        file_name = vals.get("name", "image")
        content_type = mimetypes.guess_type(file_name + ".jpg")[0] or "image/jpeg"

        client = ImageServiceFactory.create(self.env)
        result = client.upload(file_data, content_type, generate_thumbnail=True)
        if result:
            vals["image_key"] = result["key"]
            vals["thumbnail_key"] = result["thumbnail_key"]
        else:
            _logger.warning("Image Service upload failed for %s", file_name)
