from odoo import fields, models


class EstateDistrict(models.Model):
    _name = "estate.district"
    _description = "Район"
    _order = "city_id, name"

    name = fields.Char(string="Название", required=True)
    code = fields.Char(string="Код", index=True)
    krisha_name = fields.Char(
        string="Имя на Krisha",
        help=(
            "Точное имя района как пишет Krisha (например, 'Алмалинский р-н'). "
            "Используется sidecar-парсером market pricing для фильтра выдачи. "
            "Если пусто — район не используется в сборе снапшотов."
        ),
    )
    city_id = fields.Many2one(
        "estate.city",
        string="Город",
        required=True,
        ondelete="restrict",
    )
    active = fields.Boolean(string="Активен", default=True)

    street_ids = fields.One2many(
        "estate.street",
        "district_id",
        string="Улицы",
    )
