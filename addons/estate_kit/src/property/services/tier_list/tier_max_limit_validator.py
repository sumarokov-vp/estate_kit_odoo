from odoo.exceptions import ValidationError

from .tier_limit_checker import TierLimitChecker


class TierMaxLimitValidator:
    def __init__(self, limit_checker: TierLimitChecker, env) -> None:
        self._limit_checker = limit_checker
        self._env = env

    def validate_max_limit(self, records) -> None:
        Tier = self._env["estate.property.tier"]
        for rec in records:
            _min, _max = self._limit_checker.get_role_limits(rec.role)
            count = Tier.search_count([
                ("user_id", "=", rec.user_id.id),
                ("role", "=", rec.role),
            ])
            if count > _max:
                role_label = dict(Tier._fields["role"].selection)[rec.role]
                raise ValidationError(
                    f"Превышен максимум для роли «{role_label}»: "
                    f"сейчас {count}, максимум {_max}."
                )
