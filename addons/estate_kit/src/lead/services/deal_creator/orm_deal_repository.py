class OrmDealRepository:
    def __init__(self, env) -> None:
        self._env = env

    def exists_for_lead(self, lead_id: int) -> bool:
        return bool(self._env["estate.deal"].search([("lead_id", "=", lead_id)], limit=1))

    def create(self, lead) -> object:
        deal_type = lead.search_deal_type or "sale"
        return self._env["estate.deal"].create({
            "lead_id": lead.id,
            "property_id": lead.property_id.id or False,
            "client_partner_id": lead.partner_id.id or False,
            "deal_type": deal_type,
        })
