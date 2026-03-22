from .active_properties_loader import ActivePropertiesLoader
from .batch_property_scorer import BatchPropertyScorer
from .calculator import MpsCalculator
from .config import PoolScoreConfig
from .freshness import ScoringFreshnessService
from .pool_summary_logger import PoolSummaryLogger
from .protocols import IAiClient
from .scoring_message_builder import ScoringMessageBuilder
from .scoring_prompt_resolver import ScoringPromptResolver
from .scoring_response_parser import ScoringResponseParser
from .service import MarketingPoolService
from .single_property_scorer import SinglePropertyScorer
from .threshold_checker import ThresholdChecker
from .tier_bonus import TierBonusCalculator


class Factory:
    @staticmethod
    def create(env, ai_client: IAiClient) -> MarketingPoolService:
        config = PoolScoreConfig.from_env(env)
        tier_calc = TierBonusCalculator(env)
        calculator = MpsCalculator(config, tier_calc)
        return MarketingPoolService(
            env=env,
            config=config,
            loader=ActivePropertiesLoader(env),
            single_scorer=SinglePropertyScorer(calculator),
            batch_scorer=BatchPropertyScorer(config, calculator),
            threshold_checker=ThresholdChecker(),
            freshness=ScoringFreshnessService(env),
            summary_logger=PoolSummaryLogger(env),
            ai_client=ai_client,
            prompt_resolver=ScoringPromptResolver(),
            message_builder=ScoringMessageBuilder(),
            response_parser=ScoringResponseParser(),
        )
