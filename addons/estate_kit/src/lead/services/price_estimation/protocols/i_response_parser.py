from typing import Protocol


class IResponseParser(Protocol):
    def parse(self, response: str) -> float: ...
