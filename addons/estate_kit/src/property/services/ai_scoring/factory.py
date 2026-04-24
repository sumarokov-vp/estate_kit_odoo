from ....market_snapshot.services.benchmark_resolver import (
    Factory as BenchmarkResolverFactory,
)
from ....shared.services.ai_client import Factory as AiClientFactory
from ..marketing_pool import Factory as MarketingPoolFactory
from ..marketing_pool.price_block_builder import (
    Factory as PriceBlockBuilderFactory,
)
from ..marketing_pool.price_score_calculator import (
    Factory as PriceScoreCalculatorFactory,
)
from .property_data_collector import PropertyDataCollector
from .property_value_transformer import PropertyValueTransformer
from .scoring_request_logger import ScoringRequestLogger
from .service import AiScoringService


class Factory:
    @staticmethod
    def create(env) -> AiScoringService:
        ai_client = AiClientFactory.create(env)
        marketing_pool = MarketingPoolFactory.create(env, ai_client)
        value_transformer = PropertyValueTransformer()
        property_data_collector = PropertyDataCollector(value_transformer)
        scoring_request_logger = ScoringRequestLogger(marketing_pool)
        benchmark_resolver = BenchmarkResolverFactory.create(env)
        price_score_calculator = PriceScoreCalculatorFactory.create(env)
        price_block_builder = PriceBlockBuilderFactory.create(env)
        return AiScoringService(
            marketing_pool=marketing_pool,
            property_data_collector=property_data_collector,
            scoring_request_logger=scoring_request_logger,
            benchmark_resolver=benchmark_resolver,
            price_score_calculator=price_score_calculator,
            price_block_builder=price_block_builder,
            env=env,
        )
