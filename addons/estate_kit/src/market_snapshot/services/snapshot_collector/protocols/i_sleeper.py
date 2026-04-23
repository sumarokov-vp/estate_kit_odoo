from typing import Protocol


class ISleeper(Protocol):
    def sleep(self, seconds: float) -> None: ...
