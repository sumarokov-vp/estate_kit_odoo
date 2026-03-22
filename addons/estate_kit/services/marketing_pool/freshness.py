import logging
from datetime import timedelta
from typing import Any

from odoo import fields
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class ScoringFreshnessService:
    def __init__(self, env: Any):
        self.env = env

    def ensure_fresh(self, properties) -> None:
        Log = self.env["estate.kit.log"]
        CAT = "marketing_pool"
        Scoring = self.env["estate.property.scoring"]
        cutoff = fields.Datetime.now() - timedelta(days=14)

        to_score = self.env["estate.property"]
        fresh_count = 0
        for prop in properties:
            latest = prop.scoring_ids[:1]
            if not latest or latest.scored_at < cutoff:
                to_score |= prop
            else:
                fresh_count += 1

        Log.log(
            CAT,
            "AI-скоринг: %d свежих, %d требуют расчёта" % (fresh_count, len(to_score)),
        )
        self.env.cr.commit()

        if not to_score:
            return

        scored = 0
        failed = 0
        for prop in to_score:
            try:
                Scoring.score_property(prop.id)
                scored += 1
            except UserError:
                failed += 1
                _logger.warning("Failed to score property %s, skipping", prop.id)
            self.env.cr.commit()

        Log.log(
            CAT,
            "AI-скоринг завершён: %d рассчитано, %d ошибок" % (scored, failed),
            level="warning" if failed else "info",
        )
        self.env.cr.commit()
