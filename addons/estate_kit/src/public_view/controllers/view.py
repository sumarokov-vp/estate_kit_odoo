import json
import logging

from markupsafe import Markup
from odoo import http
from odoo.http import Response, request

from ...property.services.public_card_renderer import (
    Factory as PublicCardRendererFactory,
)
from ...property.services.similar_picker import Factory as SimilarPickerFactory
from ...shared.services.image_service import Factory as ImageServiceFactory
from ..services.similar_card_builder import Factory as SimilarCardBuilderFactory

_logger = logging.getLogger(__name__)

_MAIN_IMAGE_BIAS = -1000

_PUBLIC_STATES = frozenset(
    {
        "active",
        "published",
        "unpublished",
        "sold",
        "mls_listed",
        "mls_removed",
        "mls_sold",
    }
)

_SIMILAR_LIMIT = 6


class PublicViewController(http.Controller):

    @http.route(
        "/estate_kit/view/<string:token>",
        type="http",
        auth="none",
        methods=["GET"],
        csrf=False,
    )
    def view_page(self, token):
        token_record = self._get_token(token)
        if not token_record:
            return request.not_found()

        prop = token_record.property_id
        if prop.state not in _PUBLIC_STATES:
            return request.not_found()

        env = request.env
        card = PublicCardRendererFactory.create(env).render(prop, token)
        similar_recs = SimilarPickerFactory.create(env).pick(
            prop, limit=_SIMILAR_LIMIT
        )
        similar = SimilarCardBuilderFactory.create(env).build(similar_recs)

        images = self._sorted_images(prop)
        company_name, company_logo = self._company_info()
        values = {
            "property": prop,
            "token": token,
            "address": self._build_address(prop),
            "price_text": self._format_price(prop),
            "images": images,
            "images_json": Markup(self._images_json(token, images)),
            "company_name": company_name,
            "company_logo": company_logo,
            "type_label": card.type_label,
            "state_badge": card.state_badge,
            "metrics": card.metrics,
            "sections": card.sections,
            "features": card.features,
            "contact": card.contact,
            "similar": similar,
        }
        html = request.env["ir.qweb"]._render(
            "estate_kit.public_view_page", values
        )
        return Response(
            "<!DOCTYPE html>\n" + str(html),
            content_type="text/html; charset=utf-8",
        )

    @http.route(
        "/estate_kit/view/<string:token>/image/<int:image_id>",
        type="http",
        auth="none",
        methods=["GET"],
        csrf=False,
    )
    def view_image(self, token, image_id):
        return self._serve_image(token, image_id, thumbnail=False)

    @http.route(
        "/estate_kit/view/<string:token>/thumb/<int:image_id>",
        type="http",
        auth="none",
        methods=["GET"],
        csrf=False,
    )
    def view_thumbnail(self, token, image_id):
        return self._serve_image(token, image_id, thumbnail=True)

    def _serve_image(self, token, image_id, thumbnail):
        token_record = self._get_token(token)
        if not token_record:
            return request.not_found()

        image = (
            request.env["estate.property.image"]
            .sudo()
            .search(
                [
                    ("id", "=", image_id),
                    ("property_id", "=", token_record.property_id.id),
                ],
                limit=1,
            )
        )
        if not image:
            return request.not_found()

        if thumbnail:
            key = image.thumbnail_key or image.image_key
        else:
            key = image.image_key or image.thumbnail_key

        if not key:
            return request.not_found()

        client = ImageServiceFactory.create(request.env)
        result = client.download(key)
        if not result:
            return request.not_found()

        data, content_type = result
        return Response(
            data,
            content_type=content_type,
            headers={
                "Cache-Control": "public, max-age=3600",
            },
        )

    def _get_token(self, token):
        return (
            request.env["estate.property.public.view.token"]
            .sudo()
            ._validate_token(token)
        )

    @staticmethod
    def _build_address(prop):
        parts = []
        if prop.city_id:
            parts.append(prop.city_id.name)
        if prop.district_id:
            parts.append(prop.district_id.name)
        if prop.street_id:
            parts.append(prop.street_id.name)
        if prop.house_number:
            parts.append(prop.house_number)
        return ", ".join(p for p in parts if p)

    @staticmethod
    def _format_price(prop):
        if not prop.price:
            return ""
        symbol = prop.currency_id.symbol or ""
        position = prop.currency_id.position or "after"
        amount = f"{prop.price:,.0f}".replace(",", " ")
        if position == "before":
            return f"{symbol} {amount}".strip()
        return f"{amount} {symbol}".strip()

    @staticmethod
    def _sorted_images(prop):
        return prop.image_ids.sorted(
            key=lambda i: (_MAIN_IMAGE_BIAS if i.is_main else 0, i.sequence, i.id)
        )

    @staticmethod
    def _images_json(token, images):
        data = [
            {
                "full": f"/estate_kit/view/{token}/image/{img.id}",
                "thumb": f"/estate_kit/view/{token}/thumb/{img.id}",
            }
            for img in images
        ]
        return json.dumps(data)

    @staticmethod
    def _company_info():
        company = request.env["res.company"].sudo().search([], limit=1)
        if not company:
            return "Estate Kit", None
        raw = company.logo_web or company.logo
        logo = None
        if raw:
            b64 = raw.decode("ascii") if isinstance(raw, bytes) else raw
            logo = f"data:image/png;base64,{b64}"
        return company.name, logo
