import logging

import requests
from odoo import http

_logger = logging.getLogger(__name__)

YMAPS_API_URL = "https://api-maps.yandex.ru/v3/"
GEOCODER_API_URL = "https://geocode-maps.yandex.ru/1.x/"


class YmapsProxyController(http.Controller):
    @http.route("/estate_kit/ymaps.js", type="http", auth="user", cors="*")
    def ymaps_script(self, **kwargs):
        api_key = (
            http.request.env["ir.config_parameter"]
            .sudo()
            .get_param("estate_kit.yandex_geocoder_api_key", "")
        )
        if not api_key:
            return http.request.make_response(
                "// No Yandex Maps API key configured",
                headers=[("Content-Type", "application/javascript")],
            )

        # Return a loader that injects the real Yandex script from CDN.
        # Proxying the script body breaks v3 because its loader fetches
        # additional modules via relative URLs from api-maps.yandex.ru.
        loader = (
            "(function(){"
            'var s=document.createElement("script");'
            's.src="%s?apikey=%s&lang=ru_RU";'
            "document.head.appendChild(s);"
            "}());"
        ) % (YMAPS_API_URL, api_key)

        return http.request.make_response(
            loader,
            headers=[
                ("Content-Type", "application/javascript; charset=utf-8"),
                ("Cache-Control", "no-store"),
            ],
        )

    @http.route("/estate_kit/geocode", type="json", auth="user")
    def geocode(self, address):
        api_key = (
            http.request.env["ir.config_parameter"]
            .sudo()
            .get_param("estate_kit.yandex_geocoder_api_key", "")
        )
        if not api_key:
            return {"error": "API key not configured"}

        try:
            resp = requests.get(
                GEOCODER_API_URL,
                params={
                    "apikey": api_key,
                    "geocode": address,
                    "format": "json",
                    "results": "1",
                },
                timeout=10,
            )
            resp.raise_for_status()
            return resp.json()
        except Exception:
            _logger.exception("Geocoding failed for: %s", address)
            return {"error": "Geocoding request failed"}
