from odoo import api, fields, models


class EstateProperty(models.Model):
    _name = "estate.property"
    _description = "Real Estate Property"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "create_date desc"

    name = fields.Char(string="Название", required=True, tracking=True)
    description = fields.Text(string="Описание")
    active = fields.Boolean(default=True)

    property_type = fields.Selection(
        [
            ("apartment", "Квартира"),
            ("house", "Дом"),
            ("commercial", "Коммерция"),
            ("land", "Земля"),
        ],
        string="Тип объекта",
        required=True,
        default="apartment",
        tracking=True,
    )
    deal_type = fields.Selection(
        [
            ("sale", "Продажа"),
            ("rent_long", "Долгосрочная аренда"),
            ("rent_daily", "Посуточная аренда"),
        ],
        string="Тип сделки",
        required=True,
        default="sale",
        tracking=True,
    )
    state = fields.Selection(
        [
            ("new", "Новый"),
            ("active", "В работе"),
            ("deposit", "Задаток"),
            ("deal", "Сделка"),
            ("canceled", "Снят"),
            ("archived", "Архив"),
        ],
        string="Стадия",
        required=True,
        copy=False,
        default="new",
        tracking=True,
    )

    price = fields.Monetary(string="Цена", tracking=True)
    currency_id = fields.Many2one(
        "res.currency",
        default=lambda self: self.env.company.currency_id,
    )
    rooms = fields.Integer(string="Комнат")
    area_total = fields.Float(string="Площадь (м²)")

    district_id = fields.Many2one("estate.district", string="Район", tracking=True)
    street = fields.Char(string="Улица")
    house_number = fields.Char(string="Дом")

    owner_id = fields.Many2one("res.partner", string="Собственник", tracking=True)
    user_id = fields.Many2one(
        "res.users",
        string="Ответственный",
        default=lambda self: self.env.user,
        tracking=True,
    )
    listing_coordinator_id = fields.Many2one(
        "res.users",
        string="Координатор листинга",
        help="Кто внёс объект в базу",
    )
    listing_agent_id = fields.Many2one(
        "res.users",
        string="Листинг-агент",
    )

    source_id = fields.Many2one("estate.source", string="Источник")
    contract_type = fields.Selection(
        [
            ("exclusive", "Эксклюзив"),
            ("non_exclusive", "Не эксклюзив"),
        ],
        string="Тип договора",
    )
    contract_start = fields.Date(string="Начало договора")
    contract_end = fields.Date(string="Окончание договора")
    is_shared = fields.Boolean(
        string="Открытый объект",
        help="Объект доступен другим агентам",
    )

    internal_note = fields.Text(string="Внутренние заметки")
    video_url = fields.Char(string="Видео")
    instagram_url = fields.Char(string="Instagram")

    attribute_value_ids = fields.One2many(
        "estate.property.attribute.value",
        "property_id",
        string="Характеристики",
    )
    image_ids = fields.One2many(
        "estate.property.image",
        "property_id",
        string="Фотографии",
    )

    def get_attribute_value(self, code):
        attr_value = self.attribute_value_ids.filtered(
            lambda v: v.attribute_id.code == code
        )
        if not attr_value:
            return None
        return attr_value._get_value()

    def set_attribute_value(self, code, value):
        attribute = self.env["estate.attribute"].search([("code", "=", code)], limit=1)
        if not attribute:
            return

        attr_value = self.attribute_value_ids.filtered(
            lambda v: v.attribute_id.code == code
        )

        field_name = f"value_{attribute.field_type}"
        vals = {"attribute_id": attribute.id, field_name: value}

        if attr_value:
            attr_value.write(vals)
        else:
            vals["property_id"] = self.id
            self.env["estate.property.attribute.value"].create(vals)

    @api.model
    def search_by_attribute(self, code, operator, value):
        attribute = self.env["estate.attribute"].search([("code", "=", code)], limit=1)
        if not attribute:
            return self.browse()

        field_name = f"value_{attribute.field_type}"
        attr_values = self.env["estate.property.attribute.value"].search(
            [
                ("attribute_id", "=", attribute.id),
                (field_name, operator, value),
            ]
        )
        return self.browse(attr_values.mapped("property_id.id"))
