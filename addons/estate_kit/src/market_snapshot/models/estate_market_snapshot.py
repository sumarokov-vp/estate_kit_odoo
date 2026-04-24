from odoo import fields, models


class EstateMarketSnapshot(models.Model):
    _name = "estate.market.snapshot"
    _description = "Снапшот рынка недвижимости"
    _order = "collected_at desc, id desc"

    city_id = fields.Many2one(
        "estate.city",
        string="Город",
        required=True,
        ondelete="restrict",
        index=True,
    )
    district_id = fields.Many2one(
        "estate.district",
        string="Район",
        ondelete="restrict",
        index=True,
    )
    residential_complex_id = fields.Many2one(
        "estate.residential.complex",
        string="ЖК",
        ondelete="restrict",
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
        index=True,
    )
    rooms = fields.Integer(string="Комнат", help="0 — агрегат по всем комнатам")

    sample_size = fields.Integer(string="Размер выборки", required=True)
    median_price_per_sqm = fields.Float(
        string="Медиана цены за м²",
        required=True,
        digits=(16, 2),
    )
    p25_price_per_sqm = fields.Float(
        string="P25 цены за м²",
        required=True,
        digits=(16, 2),
    )
    p75_price_per_sqm = fields.Float(
        string="P75 цены за м²",
        required=True,
        digits=(16, 2),
    )
    currency = fields.Char(string="Валюта", required=True, default="KZT")
    source = fields.Char(string="Источник", required=True, default="krisha")
    collected_at = fields.Datetime(
        string="Дата сбора",
        required=True,
        default=fields.Datetime.now,
        index=True,
    )

    _sql_constraints = [
        (
            "sample_size_positive",
            "CHECK (sample_size > 0)",
            "Размер выборки должен быть положительным.",
        ),
    ]

    def init(self):
        self.env.cr.execute(
            """
            ALTER TABLE estate_market_snapshot
            ADD COLUMN IF NOT EXISTS samples_per_sqm double precision[]
            """
        )
        self.env.cr.execute(
            """
            CREATE INDEX IF NOT EXISTS estate_market_snapshot_lookup_idx
            ON estate_market_snapshot
                (city_id, district_id, property_type, rooms, collected_at DESC)
            """
        )
