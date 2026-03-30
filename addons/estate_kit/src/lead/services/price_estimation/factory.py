from ...shared.services.ai_client import Factory as AiClientFactory
from .criteria_collector import CriteriaCollector
from .prompt_builder import PromptBuilder
from .response_parser import ResponseParser
from .service import PriceEstimationService


class Factory:
    @staticmethod
    def create(env) -> PriceEstimationService:
        ai_client = AiClientFactory.create(env)
        criteria_collector = CriteriaCollector()
        prompt_builder = PromptBuilder()
        response_parser = ResponseParser()
        return PriceEstimationService(ai_client, criteria_collector, prompt_builder, response_parser)
