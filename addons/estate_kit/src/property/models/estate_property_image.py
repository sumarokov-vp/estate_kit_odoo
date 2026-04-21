from odoo import api, fields, models

from ..services.image_management import Factory as ImageManagementFactory


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
        svc = ImageManagementFactory.create(self.env)
        for vals in vals_list:
            image_data = vals.pop("image_data", None)
            if image_data and not vals.get("image_key"):
                svc.upload(vals, image_data)
        return super().create(vals_list)

    def unlink(self):
        skip_sync = self.env.context.get("skip_api_sync")
        if not skip_sync:
            ImageManagementFactory.create(self.env).delete_images(self)
        return super().unlink()
