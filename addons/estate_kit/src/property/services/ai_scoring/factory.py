from ....shared.services.ai_client import Factory as AiClientFactory
from ..marketing_pool import Factory as MarketingPoolFactory
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
        return AiScoringService(marketing_pool, property_data_collector, scoring_request_logger, env)
