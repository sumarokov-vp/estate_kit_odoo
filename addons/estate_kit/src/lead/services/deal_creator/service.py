from .protocols import IDealRepository, IParticipantCreator


class DealCreatorService:
    def __init__(self, deal_repository: IDealRepository, participant_creator: IParticipantCreator) -> None:
        self._deal_repository = deal_repository
        self._participant_creator = participant_creator

    def create_if_not_exists(self, lead) -> None:
        if self._deal_repository.exists_for_lead(lead.id):
            return
        deal = self._deal_repository.create(lead)
        self._participant_creator.create_for_deal(deal, lead)
