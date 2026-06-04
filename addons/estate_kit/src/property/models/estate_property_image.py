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
    media_type = fields.Selection(
        [("image", "Image"), ("video", "Video")],
        default="image",
    )
    image_key = fields.Char("Image Key", copy=False)
    thumbnail_key = fields.Char("Thumbnail Key", copy=False)
    video_key = fields.Char("Video Key", copy=False)
    poster_key = fields.Char("Poster Key", copy=False)
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
            video_data = vals.pop("video_data", None)
            video_content_type = vals.pop("video_content_type", None)
            if video_data and not vals.get("video_key"):
                svc.upload_video(vals, video_data, video_content_type)
        return super().create(vals_list)

    def unlink(self):
        skip_sync = self.env.context.get("skip_api_sync")
        if not skip_sync:
            ImageManagementFactory.create(self.env).delete_images(self)
        return super().unlink()
