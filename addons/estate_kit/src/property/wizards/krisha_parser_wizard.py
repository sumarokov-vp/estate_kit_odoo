from odoo import _, fields, models
from odoo.exceptions import UserError

from ..services.krisha_parser import KrishaParser, ParseParams


class KrishaParserWizard(models.TransientModel):
    _name = "krisha.parser.wizard"
    _description = "Параметры парсинга Krisha.kz"

    city_id = fields.Many2one(
        "estate.city",
        string="Город",
        default=lambda self: self.env["estate.city"].search([("code", "=", "almaty")], limit=1),
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
            city=self.city_id.code,
            rooms=self.rooms or "",
            price_from=self.price_from or 0,
            price_to=self.price_to or 0,
            has_photo=self.has_photo,
            owner=self.owner,
        )

        results = parser.parse(params, max_pages=self.max_pages)

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
                "photo_urls_csv": ",".join(item.get("photo_urls", [])),
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
