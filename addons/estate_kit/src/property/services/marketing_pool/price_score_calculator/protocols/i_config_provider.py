from typing import Protocol

from ..config import PriceScoreConfig


class IPriceScoreConfigProvider(Protocol):
    def load(self) -> PriceScoreConfig: ...
