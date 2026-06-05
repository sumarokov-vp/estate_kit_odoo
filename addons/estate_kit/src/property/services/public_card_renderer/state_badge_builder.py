from .state_badges import STATE_BADGES


class StateBadgeBuilder:
    def build(self, prop) -> dict | None:
        badge = STATE_BADGES.get(prop.state)
        return dict(badge) if badge else None
