from typing import Protocol


class IStateTransitioner(Protocol):
    def transition(
        self,
        records,
        valid_from_states: tuple[str, ...],
        to_state: str,
        error_msg: str,
    ) -> None: ...
