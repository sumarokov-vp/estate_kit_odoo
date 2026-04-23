import logging

import requests
from odoo import http

_logger = logging.getLogger(__name__)

TWOGIS_GEOCODE_URL = "https://catalog.api.2gis.com/3.0/items/geocode"


class TwoGisProxyController(http.Controller):
    @http.route("/estate_kit/twogis/api_key", type="jsonrpc", auth="user")
    def twogis_api_key(self):
        api_key = (
            http.request.env["ir.config_parameter"]
            .sudo()
            .get_param("estate_kit.twogis_api_key", "")
        )
        return {"api_key": api_key}

    @http.route("/estate_kit/geocode", type="jsonrpc", auth="user")
    def geocode(self, address):
        api_key = (
            http.request.env["ir.config_parameter"]
            .sudo()
            .get_param("estate_kit.twogis_api_key", "")
        )
        if not api_key:
            return {"error": "API key not configured"}

        try:
            resp = requests.get(
                TWOGIS_GEOCODE_URL,
                params={
                    "key": api_key,
                    "q": address,
                    "fields": "items.point",
                    "page_size": 1,
                },
                timeout=10,
            )
            resp.raise_for_status()
            data = resp.json()
            items = data.get("result", {}).get("items", [])
            if not items:
                return {"error": "not_found"}
            point = items[0].get("point") or {}
            lat = point.get("lat")
            lon = point.get("lon")
            if lat is None or lon is None:
                return {"error": "not_found"}
            return {"lat": float(lat), "lon": float(lon)}
        except Exception:
            _logger.exception("2GIS geocoding failed for: %s", address)
            return {"error": "Geocoding request failed"}
