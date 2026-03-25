from odoo.exceptions import ValidationError


class TierListService:
    def __init__(self, env) -> None:
        self._env = env

    def compute_in_my_tier_list(self, records) -> None:
        uid = self._env.uid
        for rec in records:
            rec.in_my_tier_list = any(t.user_id.id == uid for t in rec.tier_ids)

    def _get_tier_role(self) -> str | None:
        user = self._env.user
        if user.has_group("estate_kit.group_estate_team_lead"):
            return "team_lead"
        if user.has_group("estate_kit.group_estate_listing_agent"):
            return "listing_agent"
        return None

    def add_to_tier_list(self, record) -> None:
        record.ensure_one()
        role = self._get_tier_role()
        if not role:
            raise ValidationError("У вас нет роли для работы с тир-листом.")
        Tier = self._env["estate.property.tier"]
        existing = Tier.search([
            ("property_id", "=", record.id),
            ("user_id", "=", self._env.uid),
            ("role", "=", role),
        ], limit=1)
        if existing:
            raise ValidationError("Объект уже в вашем тир-листе.")
        max_priority = Tier.search([
            ("user_id", "=", self._env.uid),
            ("role", "=", role),
        ], order="priority desc", limit=1)
        next_priority = (max_priority.priority + 1) if max_priority else 1
        Tier.create({
            "property_id": record.id,
            "user_id": self._env.uid,
            "role": role,
            "priority": next_priority,
        })

    def remove_from_tier_list(self, record) -> None:
        record.ensure_one()
        role = self._get_tier_role()
        if not role:
            raise ValidationError("У вас нет роли для работы с тир-листом.")
        Tier = self._env["estate.property.tier"]
        existing = Tier.search([
            ("property_id", "=", record.id),
            ("user_id", "=", self._env.uid),
            ("role", "=", role),
        ], limit=1)
        if not existing:
            raise ValidationError("Объект не в вашем тир-листе.")
        _min, _ = existing._get_role_limits(role)
        count = Tier.search_count([
            ("user_id", "=", self._env.uid),
            ("role", "=", role),
        ])
        if count <= _min:
            raise ValidationError(
                f"Нельзя убрать — в тир-листе минимум {_min} объектов "
                f"для роли «{dict(Tier._fields['role'].selection)[role]}». "
                f"Сначала добавьте другой объект."
            )
        existing.unlink()
