from typing import Protocol


class IConfigParamReader(Protocol):
    def read_float(self, key: str, default: float) -> float: ...
