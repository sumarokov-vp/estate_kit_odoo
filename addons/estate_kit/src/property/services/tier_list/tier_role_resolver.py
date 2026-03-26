class TierRoleResolver:
    def __init__(self, env) -> None:
        self._env = env

    def get_tier_role(self) -> str | None:
        user = self._env.user
        if user.has_group("estate_kit.group_estate_team_lead"):
            return "team_lead"
        if user.has_group("estate_kit.group_estate_listing_agent"):
            return "listing_agent"
        return None
