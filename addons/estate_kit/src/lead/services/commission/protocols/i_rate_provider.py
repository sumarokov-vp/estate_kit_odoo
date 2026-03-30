from typing import Protocol


class IRateProvider(Protocol):
    def get_rate(self, lead) -> float: ...
