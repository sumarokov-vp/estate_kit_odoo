class TierLimitChecker:
    def __init__(self, env) -> None:
        self._env = env

    def get_role_limits(self, role: str) -> tuple[int, int]:
        get = self._env["ir.config_parameter"].sudo().get_param
        if role == "listing_agent":
            return (
                int(get("estate_kit.tier_min_listing_agent", "5")),
                int(get("estate_kit.tier_max_listing_agent", "15")),
            )
        if role == "team_lead":
            return (
                int(get("estate_kit.tier_min_team_lead", "20")),
                int(get("estate_kit.tier_max_team_lead", "50")),
            )
        return (0, 0)
