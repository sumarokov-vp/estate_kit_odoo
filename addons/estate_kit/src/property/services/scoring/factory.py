from ....shared.services.ai_client import Factory as AiClientFactory
from ..marketing_pool import Factory as MarketingPoolFactory
from .service import ScoringService


class Factory:
    @staticmethod
    def create(env) -> ScoringService:
        marketing_pool = MarketingPoolFactory.create(env, AiClientFactory.create(env))
        return ScoringService(marketing_pool, env)
