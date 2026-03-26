from typing import Protocol


class IStateTransitioner(Protocol):
    def transition(self, records, from_states: str | tuple, to_state: str, error_msg: str) -> None: ...
