from typing import Protocol

from ..calculator import MpsResult


class IMpsCalculator(Protocol):
    def calculate(self, prop, scoring) -> MpsResult: ...
