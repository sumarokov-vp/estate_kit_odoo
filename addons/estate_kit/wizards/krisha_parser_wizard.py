import base64
import logging

from odoo import _, api, fields, models
from odoo.exceptions import UserError

from ..services.krisha_parser import KrishaParser, ParseParams

_logger = logging.getLogger(__name__)


class KrishaParserWizard(models.TransientModel):
    _name = "krisha.parser.wizard"
    _description = "Параметры парсинга Krisha.kz"

    city = fields.Selection(
        [
            ("almaty", "Алматы"),
            ("astana", "Астана"),
            ("shymkent", "Шымкент"),
            ("aktau", "Актау"),
            ("aktobe", "Актобе"),
            ("atyrau", "Атырау"),
            ("karaganda", "Караганда"),
            ("kokshetau", "Кокшетау"),
            ("kostanay", "Костанай"),
            ("kyzylorda", "Кызылорда"),
            ("mangystau", "Мангистауская область"),
            ("pavlodar", "Павлодар"),
            ("petropavlovsk", "Петропавловск"),
            ("semey", "Семей"),
            ("taldykorgan", "Талдыкорган"),
            ("taraz", "Тараз"),
            ("turkestan", "Туркестан"),
            ("uralsk", "Уральск"),
            ("ust-kamenogorsk", "Усть-Каменогорск"),
        ],
        string="Город",
        default="almaty",
        required=True,
    )
    rooms = fields.Char(
        string="Комнаты",
        help="Через запятую, например: 1,2,3",
    )
    price_from = fields.Integer(string="Цена от")
    price_to = fields.Integer(string="Цена до")
    has_photo = fields.Boolean(string="С фото", default=True)
    owner = fields.Boolean(string="От владельца")
    max_pages = fields.Integer(string="Страниц", default=1, required=True)

    def action_parse(self):
        self.ensure_one()

        parser = KrishaParser()
        params = ParseParams(
            city=self.city,
            rooms=self.rooms or "",
            price_from=self.price_from or 0,
            price_to=self.price_to or 0,
            has_photo=self.has_photo,
            owner=self.owner,
        )

        try:
            results = parser.parse(params, max_pages=self.max_pages)
        except Exception as e:
            _logger.exception("Krisha parser error")
            raise UserError(_("Ошибка парсинга: %s") % str(e)) from e

        if not results:
            raise UserError(_("Ничего не найдено по заданным параметрам"))

        existing_urls = set(
            self.env["estate.property"]
            .search([("krisha_url", "!=", False)])
            .mapped("krisha_url")
        )

        preview = self.env["krisha.parser.preview"].create({})

        for item in results:
            url = item.get("url", "")
            is_duplicate = url in existing_urls

            self.env["krisha.parser.result"].create({
                "wizard_id": preview.id,
                "krisha_id": item.get("krisha_id"),
                "krisha_url": url,
                "title": item.get("title", ""),
                "rooms": item.get("rooms", 0),
                "area": item.get("area", 0.0),
                "floor": item.get("floor"),
                "floors_total": item.get("floors_total"),
                "price": item.get("price", 0),
                "city": item.get("city", ""),
                "address": item.get("address", ""),
                "latitude": item.get("latitude"),
                "longitude": item.get("longitude"),
                "photo_url": item.get("photo_urls", [""])[0] if item.get("photo_urls") else "",
                "photo_urls_json": ",".join(item.get("photo_urls", [])),
                "is_duplicate": is_duplicate,
                "selected": not is_duplicate,
            })

        return {
            "type": "ir.actions.act_window",
            "res_model": "krisha.parser.preview",
            "res_id": preview.id,
            "view_mode": "form",
            "target": "new",
            "context": {"form_view_initial_mode": "edit"},
        }


class KrishaParserResult(models.TransientModel):
    _name = "krisha.parser.result"
    _description = "Результат парсинга"

    wizard_id = fields.Many2one("krisha.parser.preview", ondelete="cascade")
    krisha_id = fields.Integer(string="ID на Krisha")
    krisha_url = fields.Char(string="URL")
    title = fields.Char(string="Заголовок")
    rooms = fields.Integer(string="Комнат")
    area = fields.Float(string="Площадь")
    floor = fields.Integer(string="Этаж")
    floors_total = fields.Integer(string="Этажность")
    price = fields.Integer(string="Цена")
    city = fields.Char(string="Город")
    address = fields.Char(string="Адрес")
    latitude = fields.Float(string="Широта")
    longitude = fields.Float(string="Долгота")
    photo_url = fields.Char(string="Фото URL")
    photo_urls_json = fields.Text(string="Все фото URLs")
    is_duplicate = fields.Boolean(string="Дубликат")
    selected = fields.Boolean(string="Импортировать", default=True)

    display_name_custom = fields.Char(
        compute="_compute_display_name_custom",
        string="Описание",
    )

    @api.depends("rooms", "area", "price", "is_duplicate")
    def _compute_display_name_custom(self):
        for record in self:
            duplicate_mark = " ⚠️ дубликат" if record.is_duplicate else ""
            price_formatted = f"{record.price:,}".replace(",", " ") if record.price else "0"
            record.display_name_custom = (
                f"{record.rooms}-комн, {record.area} м², {price_formatted} ₸{duplicate_mark}"
            )


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

            city_id = city_mapping.get(result.city.lower()) if result.city else False

            property_vals = {
                "name": result.title or f"{result.rooms}-комн. квартира, {result.area} м²",
                "property_type": "apartment",
                "deal_type": "sale",
                "state": "new",
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

            prop = self.env["estate.property"].create(property_vals)
            created_properties |= prop

            photo_urls = result.photo_urls_json.split(",") if result.photo_urls_json else []
            _logger.info("Initial photo_urls from result: %d", len(photo_urls))
            if details.get("photo_urls"):
                photo_urls = details["photo_urls"]
                _logger.info("Photo_urls from details: %d", len(photo_urls))

            _logger.info("Processing %d photos for property %s", len(photo_urls[:10]), prop.id)
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
                        _logger.info("Saved image %d for property %s", i + 1, prop.id)
                except Exception as e:
                    _logger.warning("Failed to download image %s: %s", photo_url, e)

        return {
            "type": "ir.actions.act_window",
            "res_model": "estate.property",
            "view_mode": "list,form",
            "domain": [("id", "in", created_properties.ids)],
            "target": "current",
            "name": _("Импортированные объекты"),
        }

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
