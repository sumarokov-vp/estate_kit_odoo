class PoolProtector:
    def __init__(self, env) -> None:
        self._env = env

    def is_pool_protected(self, prop) -> bool:
        get_param = self._env["ir.config_parameter"].sudo().get_param
        protect_priority = int(get_param("estate_kit.tier_lead_protection_priority", "5"))

        lead_tiers = prop.tier_ids.filtered(lambda t: t.role == "team_lead")
        if lead_tiers and min(t.priority for t in lead_tiers) <= protect_priority:
            return True

        active_with_leads = prop.placement_ids.filtered(
            lambda p: p.state == "active" and p.leads_count > 0
        )
        if active_with_leads:
            return True

        return False
