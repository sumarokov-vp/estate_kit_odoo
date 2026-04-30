import logging

from odoo import http
from odoo.http import Response, request

from ...shared.services.image_service import Factory as ImageServiceFactory

_logger = logging.getLogger(__name__)


class ImageController(http.Controller):
    @http.route(
        "/estate_kit/image/<path:key>",
        type="http",
        auth="user",
        methods=["GET"],
    )
    def get_image(self, key, **kwargs):
        client = ImageServiceFactory.create(request.env)
        result = client.download(key)
        if not result:
            return request.not_found()

        data, content_type = result
        return Response(
            data,
            content_type=content_type,
            headers={
                "Cache-Control": "private, max-age=3600",
            },
        )

    @http.route(
        "/estate_kit/image/rotate",
        type="json",
        auth="user",
        methods=["POST"],
    )
    def rotate_image(self, image_id, degrees, **kwargs):
        image = request.env["estate.property.image"].browse(image_id)
        if not image.exists() or not image.image_key:
            return {"success": False, "error": "Image not found"}

        client = ImageServiceFactory.create(request.env)
        result = client.rotate(image.image_key, degrees)
        if not result:
            return {"success": False, "error": "Rotation failed"}

        new_key = result["key"]
        new_thumbnail_key = result.get("thumbnail_key") or ""
        image.write({
            "image_key": new_key,
            "thumbnail_key": new_thumbnail_key or image.thumbnail_key,
        })

        return {
            "success": True,
            "full_url": f"/estate_kit/image/{new_key}",
            "thumbnail_url": (
                f"/estate_kit/image/{new_thumbnail_key}"
                if new_thumbnail_key
                else f"/estate_kit/image/{new_key}"
            ),
        }
