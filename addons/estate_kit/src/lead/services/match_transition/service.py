from datetime import datetime
from typing import Any

from .set_rejected import SetRejected
from .set_selected import SetSelected
from .set_viewed import SetViewed


class MatchTransitionService:
    def __init__(
        self,
        set_viewed: SetViewed,
        set_rejected: SetRejected,
        set_selected: SetSelected,
    ) -> None:
        self._set_viewed = set_viewed
        self._set_rejected = set_rejected
        self._set_selected = set_selected

    def transition(self, match: Any, new_state: str, now: datetime) -> None:
        if new_state == "viewed":
            self._set_viewed.execute(match, now)
        elif new_state == "rejected":
            self._set_rejected.execute(match)
        elif new_state == "selected":
            self._set_selected.execute(match)
