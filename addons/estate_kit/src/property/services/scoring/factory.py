from .....src.shared.services.anthropic_client import AnthropicClient
from ..marketing_pool import Factory as MarketingPoolFactory
from .service import ScoringService


class Factory:
    @staticmethod
    def create(env) -> ScoringService:
        marketing_pool = MarketingPoolFactory.create(env, AnthropicClient(env))
        return ScoringService(marketing_pool, env)
