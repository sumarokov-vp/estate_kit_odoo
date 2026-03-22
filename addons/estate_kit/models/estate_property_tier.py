from odoo import api, fields, models
from odoo.exceptions import ValidationError


class EstatePropertyTier(models.Model):
    _name = "estate.property.tier"
    _description = "Тир-лист объектов"
    _order = "priority, date_added desc"
    _rec_name = "property_id"

    property_id = fields.Many2one(
        "estate.property",
        string="Объект",
        required=True,
        ondelete="cascade",
    )
    user_id = fields.Many2one(
        "res.users",
        string="Пользователь",
        required=True,
        default=lambda self: self.env.uid,
        ondelete="cascade",
    )
    role = fields.Selection(
        [
            ("listing_agent", "Листинг-агент"),
            ("team_lead", "Тим-лид"),
        ],
        string="Роль",
        required=True,
    )
    priority = fields.Integer(
        string="Приоритет",
        required=True,
        default=10,
        help="1 = высший приоритет",
    )
    date_added = fields.Date(
        string="Дата добавления",
        required=True,
        default=fields.Date.context_today,
    )
    note = fields.Text(string="Комментарий")

    _sql_constraints = [
        (
            "unique_property_user_role",
            "UNIQUE(property_id, user_id, role)",
            "Объект уже добавлен в тир-лист этого пользователя для данной роли.",
        ),
        (
            "priority_positive",
            "CHECK(priority > 0)",
            "Приоритет должен быть положительным числом.",
        ),
    ]

    def _get_role_limits(self, role):
        """Возвращает (min, max) лимиты для роли из ir.config_parameter."""
        get = self.env["ir.config_parameter"].sudo().get_param
        if role == "listing_agent":
            return (
                int(get("estate_kit.tier_min_listing_agent", "5")),
                int(get("estate_kit.tier_max_listing_agent", "15")),
            )
        elif role == "team_lead":
            return (
                int(get("estate_kit.tier_min_team_lead", "20")),
                int(get("estate_kit.tier_max_team_lead", "50")),
            )
        return (0, 0)

    @api.constrains("property_id", "user_id", "role")
    def _check_tier_max_limit(self):
        for rec in self:
            _min, _max = rec._get_role_limits(rec.role)
            count = self.search_count([
                ("user_id", "=", rec.user_id.id),
                ("role", "=", rec.role),
            ])
            if count > _max:
                raise ValidationError(
                    f"Превышен максимум для роли «{dict(self._fields['role'].selection)[rec.role]}»: "
                    f"сейчас {count}, максимум {_max}."
                )
