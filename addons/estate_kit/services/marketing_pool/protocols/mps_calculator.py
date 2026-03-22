from typing import Protocol

from ..mps_result import MpsResult


class IMpsCalculator(Protocol):
    def calculate(self, prop, scoring) -> MpsResult: ...
