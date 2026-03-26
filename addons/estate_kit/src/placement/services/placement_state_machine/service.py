from .protocols import IStateTransitioner


class PlacementStateMachineService:
    def __init__(self, transitioner: IStateTransitioner):
        self._transitioner = transitioner

    def activate(self, records) -> None:
        self._transitioner.transition(
            records,
            valid_from_states=("draft", "paused"),
            to_state="active",
            error_msg="Активировать можно только черновик или приостановленное размещение.",
        )

    def pause(self, records) -> None:
        self._transitioner.transition(
            records,
            valid_from_states=("active",),
            to_state="paused",
            error_msg="Приостановить можно только активное размещение.",
        )

    def remove(self, records) -> None:
        self._transitioner.transition(
            records,
            valid_from_states=("draft", "active", "paused", "expired"),
            to_state="removed",
            error_msg="Размещение уже снято.",
        )

    def return_draft(self, records) -> None:
        self._transitioner.transition(
            records,
            valid_from_states=("paused", "removed"),
            to_state="draft",
            error_msg="Вернуть в черновик можно только приостановленное или снятое размещение.",
        )
