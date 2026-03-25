import logging
import threading

from odoo import api

from .protocols import IMarketingPool

_logger = logging.getLogger(__name__)


class ScoringService:
    def __init__(self, marketing_pool: IMarketingPool, env) -> None:
        self._marketing_pool = marketing_pool
        self._env = env

    def score_property(self, record) -> dict:
        record.ensure_one()
        self._env["estate.property.scoring"].score_property(record.id)
        self._marketing_pool.update_single(record)
        return {
            "type": "ir.actions.act_window",
            "res_model": "estate.property",
            "res_id": record.id,
            "views": [[False, "form"]],
            "target": "current",
        }

    def rpc_score_property(self, record) -> dict:
        record.ensure_one()
        scoring = self._env["estate.property.scoring"].score_property(record.id)
        self._marketing_pool.update_single(record)
        return {
            "price_score": scoring.price_score_color,
            "quality_score": scoring.quality_score_color,
            "listing_score": scoring.listing_score_color,
            "rationale": scoring.rationale,
            "pool_status": self._marketing_pool.build_pool_status(record, scoring),
        }

    def calculate_all_async(self) -> dict:
        uid = self._env.uid
        registry = self._env.registry

        def _run():
            with registry.cursor() as cr:
                env = api.Environment(cr, uid, {})
                from .....services.anthropic_client import AnthropicClient
                from .....services.marketing_pool import Factory as MarketingPoolFactory
                MarketingPoolFactory.create(env, AnthropicClient(env)).calculate_all()

        thread = threading.Thread(target=_run, daemon=True)
        thread.start()
        _logger.info("Pool score calculation started in background thread")
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "message": "Расчёт пула запущен в фоне",
                "type": "info",
                "sticky": False,
            },
        }

    def calculate_all(self) -> None:
        self._marketing_pool.calculate_all()
