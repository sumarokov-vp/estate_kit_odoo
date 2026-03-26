from .....src.shared.services.anthropic_client import AnthropicClient
from ..marketing_pool import Factory as MarketingPoolFactory
from .pool_protector import PoolProtector
from .pool_remover import PoolRemover
from .service import PoolRotationService


class Factory:
    @staticmethod
    def create(env) -> PoolRotationService:
        marketing_pool = MarketingPoolFactory.create(env, AnthropicClient(env))
        pool_protector = PoolProtector(env)
        pool_remover = PoolRemover()
        return PoolRotationService(marketing_pool, pool_protector, pool_remover, env)
