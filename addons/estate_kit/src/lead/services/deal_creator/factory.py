from .orm_deal_repository import OrmDealRepository
from .orm_participant_creator import OrmParticipantCreator
from .service import DealCreatorService


class Factory:
    @staticmethod
    def create(env) -> DealCreatorService:
        deal_repository = OrmDealRepository(env)
        participant_creator = OrmParticipantCreator(env)
        return DealCreatorService(deal_repository, participant_creator)
