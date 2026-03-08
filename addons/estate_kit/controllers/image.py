import logging

from odoo import http
from odoo.http import request, Response

from ..services.image_service_client import ImageServiceClient

_logger = logging.getLogger(__name__)


class ImageController(http.Controller):
    @http.route(
        "/estate_kit/image/<path:key>",
        type="http",
        auth="user",
        methods=["GET"],
    )
    def get_image(self, key, **kwargs):
        client = ImageServiceClient(request.env)
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
