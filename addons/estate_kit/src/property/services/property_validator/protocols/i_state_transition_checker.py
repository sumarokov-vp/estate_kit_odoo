from typing import Protocol


class IStateTransitionChecker(Protocol):
    def check_state_transition(self, records, new_state: str) -> None: ...
