import logging

from .prompt_builder import SYSTEM_PROMPT
from .protocols import IAiClient, ICriteriaCollector, IPromptBuilder, IResponseParser

_logger = logging.getLogger(__name__)


class PriceEstimationService:
    def __init__(
        self,
        ai_client: IAiClient,
        criteria_collector: ICriteriaCollector,
        prompt_builder: IPromptBuilder,
        response_parser: IResponseParser,
    ) -> None:
        self._ai_client = ai_client
        self._criteria_collector = criteria_collector
        self._prompt_builder = prompt_builder
        self._response_parser = response_parser

    def estimate(self, lead) -> float:
        if not self._ai_client.is_configured:
            return 0.0

        criteria = self._criteria_collector.collect(lead)
        if not criteria:
            return 0.0

        user_prompt = self._prompt_builder.build(criteria)
        response = self._ai_client.complete(SYSTEM_PROMPT, user_prompt)
        if response is None:
            return 0.0

        result = self._response_parser.parse(response)
        _logger.info("AI price estimation for lead %s: %s", lead.id, result)
        return result
