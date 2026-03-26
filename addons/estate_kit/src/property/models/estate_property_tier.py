from odoo import api, fields, models

from ..services.tier_list import Factory as TierListFactory
from ..services.tier_list.tier_limit_checker import TierLimitChecker


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

    def get_role_limits(self, role: str) -> tuple[int, int]:
        return TierLimitChecker(self.env).get_role_limits(role)

    @api.constrains("property_id", "user_id", "role")
    def _check_tier_max_limit(self):
        TierListFactory.create(self.env).validate_max_limit(self)
