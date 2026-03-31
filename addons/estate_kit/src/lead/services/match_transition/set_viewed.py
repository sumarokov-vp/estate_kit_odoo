from datetime import datetime
from typing import Any

from .protocols import IMatchWriter


class SetViewed:
    def __init__(self, writer: IMatchWriter, stage_id: int) -> None:
        self._writer = writer
        self._stage_id = stage_id

    def execute(self, match: Any, now: datetime) -> None:
        self._writer.write(match, {"stage_id": self._stage_id, "viewed_date": now})
