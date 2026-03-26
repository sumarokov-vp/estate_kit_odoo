import logging

from odoo.exceptions import UserError

from .protocols import IMarketingPool, IPropertyDataCollector, IScoringRequestLogger

_logger = logging.getLogger(__name__)

_LOG_CATEGORY = "ai_scoring"


class AiScoringService:
    def __init__(
        self,
        marketing_pool: IMarketingPool,
        property_data_collector: IPropertyDataCollector,
        scoring_request_logger: IScoringRequestLogger,
        env,
    ) -> None:
        self._marketing_pool = marketing_pool
        self._property_data_collector = property_data_collector
        self._scoring_request_logger = scoring_request_logger
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
        property_data = self._property_data_collector.collect(prop)

        self._scoring_request_logger.log_request(Log, prop, property_data)
        self._env.cr.commit()

        result = self._marketing_pool.score_property(property_data)
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

        scoring = self._env["estate.property.scoring"].create({
            "property_id": prop.id,
            "price_score": result["price_score"],
            "quality_score": result["quality_score"],
            "listing_score": result["listing_score"],
            "rationale": result["rationale"],
        })
        Log.log(
            _LOG_CATEGORY,
            "Ответ AI-скоринга: %s → price=%d, quality=%d, listing=%d"
            % (prop.name, scoring.price_score, scoring.quality_score, scoring.listing_score),
            details=result.get("rationale", ""),
            property_id=prop.id,
        )
        self._env.cr.commit()

        _logger.info(
            "AI scoring created for property %s: price=%s quality=%s listing=%s",
            prop.id,
            scoring.price_score,
            scoring.quality_score,
            scoring.listing_score,
        )
        return scoring
