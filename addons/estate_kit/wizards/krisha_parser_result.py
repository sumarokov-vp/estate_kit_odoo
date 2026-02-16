from odoo import api, fields, models


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
