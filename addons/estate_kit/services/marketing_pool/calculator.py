from odoo import fields

from .config import PoolScoreConfig
from .mps_result import MpsResult
from .protocols import ITierBonusCalculator


class MpsCalculator:
    def __init__(self, config: PoolScoreConfig, tier_bonus_calc: ITierBonusCalculator):
        self._config = config
        self._tier_bonus_calc = tier_bonus_calc

    def calculate(self, prop, scoring) -> MpsResult:
        avg_ai = (scoring.price_score + scoring.quality_score + scoring.listing_score) / 3.0
        tier_bonus = self._tier_bonus_calc.calculate(prop)
        mps = avg_ai * self._config.w_scoring + tier_bonus * self._config.w_tier

        if mps >= self._config.t_include:
            indicator = "🟢"
        elif mps >= self._config.t_exclude:
            indicator = "🟡"
        else:
            indicator = "🔴"

        now_str = fields.Datetime.now().strftime("%d.%m.%Y %H:%M")
        display = "%s %.1f (%s)" % (indicator, mps, now_str)

        return MpsResult(score=round(mps, 1), indicator=indicator, display=display)
