import base64
import logging

from odoo import _, api, fields, models
from odoo.exceptions import UserError

from ..services.krisha_parser import KrishaParser

_logger = logging.getLogger(__name__)


class KrishaParserPreview(models.TransientModel):
    _name = "krisha.parser.preview"
    _description = "Превью результатов парсинга"

    result_ids = fields.One2many(
        "krisha.parser.result",
        "wizard_id",
        string="Результаты",
    )
    total_found = fields.Integer(
        string="Найдено",
        compute="_compute_stats",
    )
    duplicates_count = fields.Integer(
        string="Дубликатов",
        compute="_compute_stats",
    )
    selected_count = fields.Integer(
        string="Выбрано",
        compute="_compute_stats",
    )

    @api.depends("result_ids", "result_ids.is_duplicate", "result_ids.selected")
    def _compute_stats(self):
        for record in self:
            record.total_found = len(record.result_ids)
            record.duplicates_count = len(record.result_ids.filtered("is_duplicate"))
            record.selected_count = len(record.result_ids.filtered("selected"))

    def action_import_selected(self):
        self.ensure_one()

        selected = self.result_ids.filtered("selected")
        if not selected:
            raise UserError(_("Не выбрано ни одного объекта для импорта"))

        parser = KrishaParser()
        city_mapping = self._get_city_mapping()
        created_properties = self.env["estate.property"]

        for result in selected:
            try:
                details = parser.fetch_property_details(result.krisha_url)
            except Exception as e:
                _logger.warning("Failed to fetch details for %s: %s", result.krisha_url, e)
                details = {}

            prop = self._create_property_from_result(result, details, city_mapping)
            created_properties |= prop
            self._import_photos(prop, result, details, parser)

        return {
            "type": "ir.actions.act_window",
            "res_model": "estate.property",
            "view_mode": "list,form",
            "domain": [("id", "in", created_properties.ids)],
            "target": "current",
            "name": _("Импортированные объекты"),
        }

    def _create_property_from_result(self, result, details, city_mapping):
        city_id = city_mapping.get(result.city.lower()) if result.city else False

        property_vals = {
            "name": result.title or f"{result.rooms}-комн. квартира, {result.area} м²",
            "property_type": "apartment",
            "deal_type": "sale",
            "state": "draft",
            "rooms": result.rooms,
            "area_total": result.area,
            "floor": result.floor,
            "floors_total": result.floors_total,
            "price": result.price,
            "krisha_url": result.krisha_url,
            "latitude": result.latitude,
            "longitude": result.longitude,
            "description": details.get("description", ""),
        }

        if city_id:
            property_vals["city_id"] = city_id

        return self.env["estate.property"].create(property_vals)

    def _import_photos(self, prop, result, details, parser):
        photo_urls = result.photo_urls_json.split(",") if result.photo_urls_json else []
        if details.get("photo_urls"):
            photo_urls = details["photo_urls"]

        for i, photo_url in enumerate(photo_urls[:10]):
            if not photo_url:
                continue
            try:
                image_data = parser.download_image(photo_url)
                if image_data:
                    self.env["estate.property.image"].create({
                        "property_id": prop.id,
                        "name": f"Фото {i + 1}",
                        "image": base64.b64encode(image_data).decode("utf-8"),
                        "sequence": i * 10,
                        "is_main": i == 0,
                    })
            except Exception as e:
                _logger.warning("Failed to download image %s: %s", photo_url, e)

    def _get_city_mapping(self) -> dict[str, int]:
        cities = self.env["estate.city"].search([])
        mapping: dict[str, int] = {}
        for city in cities:
            mapping[city.name.lower()] = city.id
            if city.code:
                mapping[city.code.lower()] = city.id
        return mapping

    def action_select_all(self):
        self.ensure_one()
        self.result_ids.filtered(lambda r: not r.is_duplicate).write({"selected": True})
        return {
            "type": "ir.actions.act_window",
            "res_model": self._name,
            "res_id": self.id,
            "view_mode": "form",
            "target": "new",
        }

    def action_deselect_all(self):
        self.ensure_one()
        self.result_ids.write({"selected": False})
        return {
            "type": "ir.actions.act_window",
            "res_model": self._name,
            "res_id": self.id,
            "view_mode": "form",
            "target": "new",
        }
