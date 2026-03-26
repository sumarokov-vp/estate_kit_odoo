from .protocols import IStateTransitioner


class DealStateMachineService:
    def __init__(self, state_transitioner: IStateTransitioner) -> None:
        self._state_transitioner = state_transitioner

    def confirm(self, records) -> None:
        self._state_transitioner.transition(
            records, "draft", "confirmed",
            "Подтвердить можно только сделку в статусе черновика.",
        )

    def start(self, records) -> None:
        self._state_transitioner.transition(
            records, "confirmed", "in_progress",
            "Начать работу можно только по подтверждённой сделке.",
        )

    def closing(self, records) -> None:
        self._state_transitioner.transition(
            records, "in_progress", "closing",
            "Перевести в закрытие можно только сделку в работе.",
        )

    def complete(self, records) -> None:
        self._state_transitioner.transition(
            records, "closing", "done",
            "Завершить можно только сделку в статусе закрытия.",
        )

    def cancel(self, records) -> None:
        self._state_transitioner.transition(
            records,
            ("draft", "confirmed", "in_progress", "closing"),
            "cancelled",
            "Отменить можно только активную сделку.",
        )
