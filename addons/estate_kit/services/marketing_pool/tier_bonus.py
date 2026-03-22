from typing import Any


class TierBonusCalculator:
    def __init__(self, env: Any):
        self.env = env

    def calculate(self, prop) -> float:
        tiers = prop.tier_ids
        if not tiers:
            return 0.0

        has_agent = any(t.role == "listing_agent" for t in tiers)
        has_lead = any(t.role == "team_lead" for t in tiers)

        if has_agent and has_lead:
            base_bonus = 8.0
        elif has_lead:
            base_bonus = 6.0
        elif has_agent:
            base_bonus = 4.0
        else:
            return 0.0

        best_tier = min(tiers, key=lambda t: t.priority)
        role = best_tier.role
        same_role_tiers = self.env["estate.property.tier"].search_count([
            ("user_id", "=", best_tier.user_id.id),
            ("role", "=", role),
        ])
        p_max = max(same_role_tiers, 1)
        multiplier = 1.0 + (1 - best_tier.priority / p_max) * 0.25
        result = base_bonus * multiplier
        return min(max(result, 0.0), 10.0)
