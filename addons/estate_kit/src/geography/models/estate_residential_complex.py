from odoo import api, fields, models
from odoo.exceptions import ValidationError


class EstateResidentialComplex(models.Model):
    _name = "estate.residential.complex"
    _description = "Жилой комплекс"
    _order = "sequence, name"

    name = fields.Char(string="Название", required=True, index=True)
    city_id = fields.Many2one(
        "estate.city",
        string="Город",
        ondelete="restrict",
        index=True,
    )
    krisha_complex_id = fields.Integer(
        string="ID ЖК на Krisha",
        index=True,
    )
    krisha_url = fields.Char(string="Ссылка Krisha")
    sequence = fields.Integer(string="Порядок", default=10)
    active = fields.Boolean(string="Активен", default=True)

    def init(self):
        self.env.cr.execute(
            """
            CREATE UNIQUE INDEX IF NOT EXISTS
            estate_residential_complex_krisha_id_uniq
            ON estate_residential_complex (krisha_complex_id)
            WHERE krisha_complex_id > 0
            """
        )

    @api.constrains("krisha_complex_id")
    def _check_krisha_complex_id_unique(self):
        for record in self:
            if not record.krisha_complex_id:
                continue
            duplicate = self.search(
                [
                    ("krisha_complex_id", "=", record.krisha_complex_id),
                    ("id", "!=", record.id),
                ],
                limit=1,
            )
            if duplicate:
                raise ValidationError(
                    f"ЖК с krisha_complex_id={record.krisha_complex_id} уже существует: {duplicate.name}"
                )
