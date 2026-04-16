import base64
import json
import logging
import os

from odoo import http
from odoo.http import Response, request

_logger = logging.getLogger(__name__)

TEMPLATE_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "..", "static", "photo_upload", "upload.html"
)


class PhotoUploadController(http.Controller):

    @http.route(
        "/estate_kit/upload/<string:token>",
        type="http",
        auth="none",
        methods=["GET"],
        csrf=False,
    )
    def upload_page(self, token):
        token_record = self._get_token(token)
        if not token_record:
            return self._error_page("Ссылка недействительна или истекла")

        prop = token_record.property_id
        address_parts = []
        if prop.city_id:
            address_parts.append(prop.city_id.name)
        if prop.district_id:
            address_parts.append(prop.district_id.name)
        if prop.street_id:
            address_parts.append(prop.street_id.name)
        if prop.house_number:
            address_parts.append(prop.house_number)
        address = ", ".join(address_parts)

        config = request.env["ir.config_parameter"].sudo()
        base_url = config.get_param("web.base.url") or ""
        company = request.env["res.company"].sudo().search([], limit=1)
        company_name = company.name if company else "Estate Kit"

        with open(TEMPLATE_PATH) as f:
            html = f.read()

        html = (
            html.replace("{property_name}", self._escape(prop.name or ""))
            .replace("{property_address}", self._escape(address))
            .replace("{token}", self._escape(token))
            .replace("{upload_url}", f"{base_url}/estate_kit/upload/{token}")
            .replace("{base_url}", self._escape(base_url))
            .replace("{company_name}", self._escape(company_name))
        )

        return Response(html, content_type="text/html; charset=utf-8")

    @http.route(
        "/estate_kit/upload/<string:token>",
        type="http",
        auth="none",
        methods=["POST"],
        csrf=False,
    )
    def upload_photo(self, token, **kw):
        token_record = self._get_token(token)
        if not token_record:
            return Response(
                json.dumps({"error": "Ссылка недействительна или истекла"}),
                status=403,
                content_type="application/json",
            )

        photo = request.httprequest.files.get("photo")
        if not photo:
            return Response(
                json.dumps({"error": "Файл не найден"}),
                status=400,
                content_type="application/json",
            )

        content_type = photo.content_type or ""
        if not content_type.startswith("image/"):
            return Response(
                json.dumps({"error": "Допускаются только изображения"}),
                status=400,
                content_type="application/json",
            )

        file_data = photo.read()
        max_size = 20 * 1024 * 1024
        if len(file_data) > max_size:
            return Response(
                json.dumps({"error": "Файл слишком большой (макс. 20 МБ)"}),
                status=400,
                content_type="application/json",
            )

        image_b64 = base64.b64encode(file_data).decode("ascii")
        property_id = token_record.property_id.id

        try:
            request.env["estate.property.image"].sudo().create(
                {
                    "property_id": property_id,
                    "name": photo.filename or "photo",
                    "image": image_b64,
                }
            )
        except Exception:
            _logger.exception("Failed to upload photo for property %s", property_id)
            return Response(
                json.dumps({"error": "Ошибка загрузки"}),
                status=500,
                content_type="application/json",
            )

        return Response(
            json.dumps({"success": True}),
            content_type="application/json",
        )

    def _get_token(self, token):
        return (
            request.env["estate.property.upload.token"]
            .sudo()
            ._validate_token(token)
        )

    @staticmethod
    def _escape(text):
        return (
            text.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
            .replace("'", "&#x27;")
        )

    @staticmethod
    def _error_page(message):
        html = f"""<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Ошибка</title>
<style>
body {{
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto,
    sans-serif;
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  margin: 0;
  background: #f5f5f5;
}}
.error {{ text-align: center; padding: 2rem; }}
.error h1 {{ color: #dc3545; font-size: 1.5rem; }}
</style>
</head>
<body>
<div class="error">
<h1>{message}</h1>
<p>Запросите новую ссылку для загрузки фотографий.</p>
</div>
</body>
</html>"""
        return Response(html, content_type="text/html; charset=utf-8", status=403)
