import base64
import json
import logging

from odoo import http
from odoo.http import request, Response

_logger = logging.getLogger(__name__)


class ImageUploadController(http.Controller):

    @http.route(
        "/estate_kit/upload_image",
        type="http",
        auth="user",
        methods=["POST"],
        csrf=False,
    )
    def upload_image(self):
        property_id = request.params.get("property_id")
        if not property_id:
            return Response('{"error": "property_id required"}', status=400, content_type="application/json")

        uploaded_file = request.httprequest.files.get("file")
        if not uploaded_file:
            return Response('{"error": "file required"}', status=400, content_type="application/json")

        try:
            property_id = int(property_id)
        except (ValueError, TypeError):
            return Response('{"error": "invalid property_id"}', status=400, content_type="application/json")

        prop = request.env["estate.property"].browse(property_id).exists()
        if not prop:
            return Response('{"error": "property not found"}', status=404, content_type="application/json")

        file_data = uploaded_file.read()
        file_name = uploaded_file.filename or "image.jpg"
        file_b64 = base64.b64encode(file_data).decode("ascii")

        sequence = request.params.get("sequence", 10)

        image_record = request.env["estate.property.image"].with_context(
            upload_raw_binary=file_b64,
        ).create({
            "property_id": property_id,
            "name": file_name.rsplit(".", 1)[0] if "." in file_name else file_name,
            "sequence": int(sequence),
        })

        return Response(
            json.dumps({
                "id": image_record.id,
                "external_id": image_record.external_id,
                "image_url": image_record.image_url or "",
                "thumbnail_url": f"/web/image/estate.property.image/{image_record.id}/thumbnail",
            }),
            status=200,
            content_type="application/json",
        )
