import logging

from odoo.exceptions import UserError

from .protocols import (
    IBenchmarkResolver,
    IMarketingPool,
    IPriceScoreCalculator,
    IPropertyDataCollector,
    IScoringRequestLogger,
)

_logger = logging.getLogger(__name__)

_LOG_CATEGORY = "ai_scoring"


class AiScoringService:
    def __init__(
        self,
        marketing_pool: IMarketingPool,
        property_data_collector: IPropertyDataCollector,
        scoring_request_logger: IScoringRequestLogger,
        benchmark_resolver: IBenchmarkResolver,
        price_score_calculator: IPriceScoreCalculator,
        env,
    ) -> None:
        self._marketing_pool = marketing_pool
        self._property_data_collector = property_data_collector
        self._scoring_request_logger = scoring_request_logger
        self._benchmark_resolver = benchmark_resolver
        self._price_score_calculator = price_score_calculator
        self._env = env

    def score(self, property_id: int):
        prop = self._env["estate.property"].browse(property_id)
        if not prop.exists():
            raise UserError("Объект не найден.")

        if not self._marketing_pool.is_configured:
            raise UserError(
                "API-ключ Anthropic не настроен. "
                "Перейдите в Настройки → Estate Kit → AI-скоринг."
            )

        Log = self._env["estate.kit.log"]

        benchmark = self._benchmark_resolver.resolve(prop)
        price_score_result = None
        if benchmark is not None:
            price_score_result = self._price_score_calculator.calculate(prop, benchmark)

        property_data = self._property_data_collector.collect(prop, benchmark)
        if price_score_result is not None:
            property_data["price_evaluation"] = {
                "score": price_score_result.score,
                "deviation": price_score_result.deviation,
                "expected_per_sqm": price_score_result.expected_per_sqm,
                "actual_per_sqm": price_score_result.actual_per_sqm,
                "hedonic_factors_applied": price_score_result.hedonic_factors_applied,
            }

        self._scoring_request_logger.log_request(Log, prop, property_data)
        self._env.cr.commit()

        with_benchmark = price_score_result is not None
        result = self._marketing_pool.score_property(
            property_data, with_benchmark=with_benchmark,
        )
        if result is None:
            Log.log(
                _LOG_CATEGORY,
                "Ошибка AI-скоринга: %s" % prop.name,
                level="error",
                property_id=prop.id,
            )
            self._env.cr.commit()
            raise UserError(
                "Не удалось получить оценку от AI. Проверьте логи сервера."
            )

        if price_score_result is not None:
            price_score = price_score_result.score
        else:
            price_score = result.get("price_score", 1)
            rationale_suffix = (
                "\n\n[Оценка без рыночных данных: нет снапшота рынка для района/типа]"
            )
            result["rationale"] = (result.get("rationale") or "") + rationale_suffix

        scoring = self._env["estate.property.scoring"].create({
            "property_id": prop.id,
            "price_score": price_score,
            "quality_score": result["quality_score"],
            "listing_score": result["listing_score"],
            "rationale": result["rationale"],
        })

        price_source = "формула" if price_score_result is not None else "LLM"
        Log.log(
            _LOG_CATEGORY,
            "Ответ AI-скоринга: %s → price=%d (%s), quality=%d, listing=%d"
            % (
                prop.name,
                scoring.price_score,
                price_source,
                scoring.quality_score,
                scoring.listing_score,
            ),
            details=result.get("rationale", ""),
            property_id=prop.id,
        )
        self._env.cr.commit()

        _logger.info(
            "AI scoring created for property %s: price=%s (%s) quality=%s listing=%s",
            prop.id,
            scoring.price_score,
            price_source,
            scoring.quality_score,
            scoring.listing_score,
        )
        return scoring
