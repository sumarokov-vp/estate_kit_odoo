from .....services.anthropic_client import AnthropicClient
from .....services.marketing_pool import Factory as MarketingPoolFactory
from .service import PoolRotationService


class Factory:
    @staticmethod
    def create(env) -> PoolRotationService:
        marketing_pool = MarketingPoolFactory.create(env, AnthropicClient(env))
        return PoolRotationService(marketing_pool, env)
