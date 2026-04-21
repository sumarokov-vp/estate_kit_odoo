import json
import logging

from odoo import http
from odoo.http import Response, request

from ...shared.services.image_service import Factory as ImageServiceFactory

_logger = logging.getLogger(__name__)

_MAIN_IMAGE_BIAS = -1000


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
        images = self._sorted_images(prop)
        values = {
            "property": prop,
            "token": token,
            "address": self._build_address(prop),
            "price_text": self._format_price(prop),
            "characteristics": self._collect_characteristics(prop),
            "features": self._collect_features(prop),
            "images": images,
            "images_json": self._images_json(token, images),
            "company_name": self._company_name(),
        }
        return request.render(
            "estate_kit.public_view_page",
            values,
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
    def _company_name():
        company = request.env["res.company"].sudo().search([], limit=1)
        return company.name if company else "Estate Kit"

    @classmethod
    def _collect_characteristics(cls, prop):
        rows = []
        cls._append(rows, "Тип объекта", cls._sel_label(prop, "property_type"))
        cls._append(rows, "Тип сделки", cls._sel_label(prop, "deal_type"))
        if prop.rooms:
            cls._append(rows, "Комнат", str(prop.rooms))
        if prop.bedrooms:
            cls._append(rows, "Спален", str(prop.bedrooms))
        if prop.area_total:
            cls._append(rows, "Общая площадь", f"{prop.area_total:g} м²")
        if prop.area_living:
            cls._append(rows, "Жилая площадь", f"{prop.area_living:g} м²")
        if prop.area_kitchen:
            cls._append(rows, "Площадь кухни", f"{prop.area_kitchen:g} м²")
        if prop.area_land:
            cls._append(rows, "Площадь участка", f"{prop.area_land:g} соток")
        if prop.floor or prop.floors_total:
            floor = prop.floor or "—"
            total = prop.floors_total or "—"
            cls._append(rows, "Этаж", f"{floor} / {total}")
        if prop.year_built:
            cls._append(rows, "Год постройки", str(prop.year_built))
        cls._append(rows, "Тип строения", cls._sel_label(prop, "building_type"))
        cls._append(rows, "Материал стен", cls._sel_label(prop, "wall_material"))
        if prop.ceiling_height:
            cls._append(rows, "Высота потолков", f"{prop.ceiling_height:g} м")
        cls._append(rows, "Состояние", cls._sel_label(prop, "condition"))
        cls._append(rows, "Санузел", cls._sel_label(prop, "bathroom"))
        if prop.bathroom_count:
            cls._append(rows, "Количество санузлов", str(prop.bathroom_count))
        cls._append(rows, "Балкон", cls._sel_label(prop, "balcony"))
        cls._append(rows, "Парковка", cls._sel_label(prop, "parking"))
        cls._append(rows, "Мебель", cls._sel_label(prop, "furniture"))
        cls._append(rows, "Отопление", cls._sel_label(prop, "heating"))
        cls._append(rows, "Водоснабжение", cls._sel_label(prop, "water"))
        cls._append(rows, "Канализация", cls._sel_label(prop, "sewage"))
        cls._append(rows, "Газ", cls._sel_label(prop, "gas"))
        cls._append(rows, "Интернет", cls._sel_label(prop, "internet"))
        if prop.residential_complex:
            cls._append(rows, "Жилой комплекс", prop.residential_complex)
        return rows

    @staticmethod
    def _collect_features(prop):
        bools = [
            ("security_intercom", "Домофон"),
            ("security_guard", "Охрана"),
            ("security_video", "Видеонаблюдение"),
            ("security_concierge", "Консьерж"),
            ("isolated_rooms", "Изолированные комнаты"),
            ("storage", "Кладовка"),
            ("quiet_yard", "Тихий двор"),
            ("kitchen_studio", "Кухня-студия"),
            ("new_plumbing", "Новая сантехника"),
            ("built_in_kitchen", "Встроенная кухня"),
            ("balcony_glazed", "Балкон застеклён"),
            ("not_corner", "Не угловая"),
        ]
        features = [label for field, label in bools if getattr(prop, field, False)]
        features.extend(e.name for e in prop.climate_equipment_ids)
        features.extend(a.name for a in prop.appliance_ids)
        features.extend(t.name for t in prop.tag_ids)
        return features

    @staticmethod
    def _append(rows, label, value):
        if value:
            rows.append((label, value))

    @staticmethod
    def _sel_label(prop, field_name):
        value = getattr(prop, field_name, False)
        if not value:
            return None
        selection = prop._fields[field_name].selection
        if callable(selection):
            selection = selection(prop)
        return dict(selection).get(value)
