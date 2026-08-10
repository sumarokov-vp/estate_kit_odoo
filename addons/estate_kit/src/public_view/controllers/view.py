import json
import logging

from markupsafe import Markup
from odoo import http
from odoo.http import Response, request
from werkzeug.utils import redirect as _wz_redirect

from ...property.services.public_card_renderer import (
    Factory as PublicCardRendererFactory,
)
from ...property.services.similar_picker import Factory as SimilarPickerFactory
from ...shared.services.image_service import Factory as ImageServiceFactory
from ..services.property_presenter import Factory as PropertyPresenterFactory
from ..services.similar_card_builder import Factory as SimilarCardBuilderFactory
from ..services.stub_page_builder import Factory as StubPageBuilderFactory

_logger = logging.getLogger(__name__)

_MAIN_IMAGE_BIAS = -1000

_SIMILAR_LIMIT = 6

_MAP_ZOOM = 17

_MAP_EMBED_URL = (
    "https://yandex.kz/map-widget/v1/"
    "?ll={lon},{lat}&z={zoom}&pt={lon},{lat},pm2rdm&lang=ru_RU"
)

_MAP_EXTERNAL_URL = "https://2gis.kz/geo/{lon},{lat}"


class PublicViewController(http.Controller):

    @http.route(
        "/estate_kit/view/<string:token>",
        type="http",
        auth="none",
        methods=["GET"],
        csrf=False,
    )
    def view_page(self, token):
        env = request.env
        stub_builder = StubPageBuilderFactory.create(env)

        token_record = self._get_token(token)
        if not token_record:
            return self._render_stub(stub_builder.build_for_invalid_link())

        prop = token_record.property_id
        stub = stub_builder.build_for_property(prop)
        if stub:
            return self._render_stub(stub)

        card = PublicCardRendererFactory.create(env).render(prop, token)
        similar_recs = SimilarPickerFactory.create(env).pick(
            prop, limit=_SIMILAR_LIMIT
        )
        similar = SimilarCardBuilderFactory.create(env).build(similar_recs)

        presenter = PropertyPresenterFactory.create(env)
        images = self._sorted_images(prop)
        company_name, company_logo = self._company_info()
        values = {
            "property": prop,
            "token": token,
            "address": presenter.address(prop),
            "price_text": presenter.price_text(prop),
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
            "map_links": self._map_links(prop),
        }
        return self._render_page("estate_kit.public_view_page", values)

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

    @http.route(
        "/estate_kit/view/<string:token>/video/<int:image_id>",
        type="http",
        auth="none",
        methods=["GET"],
        csrf=False,
    )
    def view_video(self, token, image_id):
        image = self._find_image(token, image_id)
        if not image.video_key:
            raise request.not_found()

        url = ImageServiceFactory.create(request.env).get_video_url(image.video_key)
        if not url:
            raise request.not_found()

        return _wz_redirect(url, code=302)

    def _find_image(self, token, image_id):
        token_record = self._get_token(token)
        if not token_record:
            raise request.not_found()

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
            raise request.not_found()
        return image

    def _serve_image(self, token, image_id, thumbnail):
        image = self._find_image(token, image_id)

        if thumbnail:
            key = image.thumbnail_key or image.image_key or image.poster_key
        else:
            key = image.image_key or image.thumbnail_key or image.poster_key

        if not key:
            raise request.not_found()

        client = ImageServiceFactory.create(request.env)
        result = client.download(key)
        if not result:
            raise request.not_found()

        data, content_type = result
        return Response(
            data,
            content_type=content_type,
            headers={
                "Cache-Control": "public, max-age=3600",
            },
        )

    @classmethod
    def _render_stub(cls, stub):
        company_name, company_logo = cls._company_info()
        values = {
            "stub": stub,
            "company_name": company_name,
            "company_logo": company_logo,
        }
        return cls._render_page("estate_kit.public_view_stub", values)

    @staticmethod
    def _render_page(template, values):
        html = request.env["ir.qweb"]._render(template, values)
        return Response(
            "<!DOCTYPE html>\n" + str(html),
            content_type="text/html; charset=utf-8",
        )

    def _get_token(self, token):
        return (
            request.env["estate.property.public.view.token"]
            .sudo()
            ._validate_token(token)
        )

    @staticmethod
    def _map_links(prop):
        if not prop.latitude or not prop.longitude:
            return None
        coords = {
            "lat": f"{prop.latitude:.7f}".rstrip("0").rstrip("."),
            "lon": f"{prop.longitude:.7f}".rstrip("0").rstrip("."),
        }
        return {
            "embed_url": _MAP_EMBED_URL.format(zoom=_MAP_ZOOM, **coords),
            "external_url": _MAP_EXTERNAL_URL.format(**coords),
        }

    @staticmethod
    def _sorted_images(prop):
        return prop.image_ids.sorted(
            key=lambda i: (_MAIN_IMAGE_BIAS if i.is_main else 0, i.sequence, i.id)
        )

    @staticmethod
    def _images_json(token, images):
        data = []
        for img in images:
            item = {
                "kind": "video" if img.media_type == "video" else "image",
                "full": f"/estate_kit/view/{token}/image/{img.id}",
                "thumb": f"/estate_kit/view/{token}/thumb/{img.id}",
            }
            if item["kind"] == "video":
                item["video"] = f"/estate_kit/view/{token}/video/{img.id}"
            data.append(item)
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
