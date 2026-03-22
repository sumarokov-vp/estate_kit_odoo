from typing import Any

from .config import PoolScoreConfig
from .protocols import (
    IActivePropertiesLoader,
    IAiClient,
    IBatchPropertyScorer,
    IFreshnessChecker,
    IMessageBuilder,
    IPoolSummaryLogger,
    IPromptResolver,
    IResponseParser,
    ISinglePropertyScorer,
    IThresholdChecker,
)


class MarketingPoolService:
    def __init__(
        self,
        env,
        config: PoolScoreConfig,
        loader: IActivePropertiesLoader,
        single_scorer: ISinglePropertyScorer,
        batch_scorer: IBatchPropertyScorer,
        threshold_checker: IThresholdChecker,
        freshness: IFreshnessChecker,
        summary_logger: IPoolSummaryLogger,
        ai_client: IAiClient,
        prompt_resolver: IPromptResolver,
        message_builder: IMessageBuilder,
        response_parser: IResponseParser,
    ):
        self._env = env
        self._config = config
        self._loader = loader
        self._single_scorer = single_scorer
        self._batch_scorer = batch_scorer
        self._threshold_checker = threshold_checker
        self._freshness = freshness
        self._summary_logger = summary_logger
        self._ai_client = ai_client
        self._prompt_resolver = prompt_resolver
        self._message_builder = message_builder
        self._response_parser = response_parser

    # --- Pool ---

    def calculate_all(self) -> None:
        Log = self._env["estate.kit.log"]
        CAT = "marketing_pool"

        properties = self._loader.load()
        if not properties:
            Log.log(CAT, "Нет активных объектов для расчёта", level="warning")
            return

        Log.log(
            CAT,
            "Расчёт пула запущен: %d объектов" % len(properties),
            details="W_scoring=%.2f, W_tier=%.2f, "
                    "мин. price=%d, мин. quality=%d, мин. listing=%d, "
                    "порог включения=%.1f, порог исключения=%.1f"
                    % (
                        self._config.w_scoring,
                        self._config.w_tier,
                        self._config.min_price,
                        self._config.min_quality,
                        self._config.min_listing,
                        self._config.t_include,
                        self._config.t_exclude,
                    ),
        )
        self._env.cr.commit()

        self._freshness.ensure_fresh(properties)

        stats, details_lines = self._batch_scorer.score_all(properties)
        self._summary_logger.log(stats, details_lines)

    def update_single(self, prop) -> None:
        self._single_scorer.update(prop)

    def scores_below_threshold(
        self, scoring, min_price: int, min_quality: int, min_listing: int,
    ) -> bool:
        return self._threshold_checker.scores_below_threshold(
            scoring, min_price, min_quality, min_listing,
        )

    # --- AI Scoring ---

    @property
    def is_configured(self) -> bool:
        return self._ai_client.is_configured

    @property
    def model(self) -> str:
        return self._ai_client.model

    def score_property(self, property_data: dict[str, Any]) -> dict[str, Any] | None:
        if not self.is_configured:
            return None

        prop_type = property_data.get("property_type", "apartment")
        system_prompt = self._prompt_resolver.resolve(prop_type)
        user_message = self._message_builder.build(property_data)

        response_text = self._ai_client.complete(system_prompt, user_message)
        if response_text is None:
            return None

        return self._response_parser.parse(response_text)
