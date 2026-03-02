import base64
import io
import logging

from odoo import api, fields, models

from ..services.image_sync_service import ImageSyncService

_logger = logging.getLogger(__name__)

THUMBNAIL_SIZE = (256, 256)


def _make_thumbnail(image_b64):
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
    image = fields.Binary(attachment=True)
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
        for vals in vals_list:
            raw_b64 = self.env.context.get("upload_raw_binary") or vals.pop("image", None)

            if raw_b64:
                vals["image"] = raw_b64
                vals["thumbnail"] = _make_thumbnail(raw_b64)

        return super().create(vals_list)

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
