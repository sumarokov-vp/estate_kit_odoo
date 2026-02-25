import base64
import io
import logging

from odoo import api, fields, models

from ..services.image_sync_service import ImageSyncService

_logger = logging.getLogger(__name__)

THUMBNAIL_SIZE = (256, 256)


def _make_thumbnail(image_b64):
    """Generate a 256x256 thumbnail from base64-encoded image data."""
    try:
        from PIL import Image
    except ImportError:
        _logger.warning("Pillow not installed, storing image as-is")
        return image_b64

    raw = base64.b64decode(image_b64)
    img = Image.open(io.BytesIO(raw))
    img.thumbnail(THUMBNAIL_SIZE, Image.LANCZOS)

    buf = io.BytesIO()
    fmt = img.format or "JPEG"
    if fmt.upper() == "JPEG":
        img = img.convert("RGB")
    img.save(buf, format=fmt, quality=85)
    return base64.b64encode(buf.getvalue()).decode("ascii")


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
    thumbnail = fields.Binary(attachment=True)
    sequence = fields.Integer(default=10)
    is_main = fields.Boolean(
        string="Main Image",
        help="This image will be used as the property thumbnail",
    )
    external_id = fields.Integer("API Image ID", index=True, copy=False)
    image_url = fields.Char("S3 URL", copy=False)

    @api.model_create_multi
    def create(self, vals_list):
        service = None
        if not self.env.context.get("skip_api_sync"):
            service = ImageSyncService(self.env)

        for vals in vals_list:
            # Get the raw full-size binary: either from context (controller upload)
            # or from legacy 'image' field in vals
            raw_b64 = self.env.context.get("upload_raw_binary") or vals.pop("image", None)

            if raw_b64 and service and vals.get("property_id"):
                # Push full-size to API, get back external_id and URL
                prop = self.env["estate.property"].browse(vals["property_id"])
                if prop.external_id:
                    result = service.push_image_binary(
                        raw_b64,
                        vals.get("name") or "image",
                        prop.external_id,
                    )
                    if result:
                        vals["external_id"] = result.get("id", 0)
                        vals["image_url"] = result.get("url", "")

            if raw_b64:
                vals["thumbnail"] = _make_thumbnail(raw_b64)

        records = super().create(vals_list)
        return records

    def unlink(self):
        images_to_delete = [
            (rec.external_id, rec.property_id.external_id)
            for rec in self
            if rec.external_id and not self.env.context.get("skip_api_sync")
        ]
        result = super().unlink()
        if images_to_delete:
            service = ImageSyncService(self.env)
            service.delete_images(images_to_delete)
        return result
