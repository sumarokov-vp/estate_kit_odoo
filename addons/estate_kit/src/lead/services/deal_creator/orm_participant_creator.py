class OrmParticipantCreator:
    def __init__(self, env) -> None:
        self._env = env

    def create_for_deal(self, deal, lead) -> None:
        participants = []
        if lead.isa_user_id:
            participants.append({"deal_id": deal.id, "role": "isa", "user_id": lead.isa_user_id.id})
        if lead.buyer_agent_id:
            participants.append({"deal_id": deal.id, "role": "buyer_agent", "user_id": lead.buyer_agent_id.id})
        if lead.transaction_coordinator_id:
            participants.append({
                "deal_id": deal.id, "role": "coordinator", "user_id": lead.transaction_coordinator_id.id,
            })
        if participants:
            self._env["estate.deal.participant"].create(participants)
