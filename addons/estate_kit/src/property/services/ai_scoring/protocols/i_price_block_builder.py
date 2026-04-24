from typing import Protocol

from ...marketing_pool.price_block_builder.result import PriceBlock
from ...marketing_pool.price_score_calculator.result import PriceScoreResult


class IPriceBlockBuilder(Protocol):
    def build(
        self,
        prop,
        benchmark,
        price_score_result: PriceScoreResult,
    ) -> PriceBlock: ...
