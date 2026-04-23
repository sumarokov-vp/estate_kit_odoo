from odoo import fields, models


class EstateMarketSnapshotConfig(models.Model):
    _name = "estate.market.snapshot.config"
    _description = "Конфигурация сбора снапшотов рынка"
    _order = "city_id, district_id, property_type, rooms"

    city_id = fields.Many2one(
        "estate.city",
        string="Город",
        required=True,
        ondelete="cascade",
    )
    district_id = fields.Many2one(
        "estate.district",
        string="Район",
        ondelete="cascade",
        domain="[('city_id', '=', city_id)]",
        help="Пусто — срез по всему городу",
    )
    property_type = fields.Selection(
        [
            ("apartment", "Квартира"),
            ("house", "Дом"),
            ("townhouse", "Таунхаус"),
            ("commercial", "Коммерция"),
            ("land", "Земля"),
        ],
        string="Тип объекта",
        required=True,
        default="apartment",
    )
    rooms = fields.Integer(
        string="Комнат",
        default=0,
        help="0 — агрегат по всем комнатам",
    )
    max_pages = fields.Integer(
        string="Макс. страниц",
        default=5,
        help="Сколько страниц листинга Krisha обходить для этого среза",
    )
    active = fields.Boolean(string="Активна", default=True)

    _sql_constraints = [
        (
            "max_pages_positive",
            "CHECK (max_pages > 0)",
            "Количество страниц должно быть положительным.",
        ),
    ]
