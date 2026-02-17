from odoo import api, fields, models

from ..services.image_sync_service import ImageSyncService


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
            service = ImageSyncService(self.env)
            for record in records:
                service.push_image(record)
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
