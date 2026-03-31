from typing import Any

from .protocols import IMatchWriter


class SetRejected:
    def __init__(self, writer: IMatchWriter, stage_id: int) -> None:
        self._writer = writer
        self._stage_id = stage_id

    def execute(self, match: Any) -> None:
        self._writer.write(match, {"stage_id": self._stage_id})
