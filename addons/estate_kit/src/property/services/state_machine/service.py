from .protocols import IApiActionCaller, IApiSync, IStateTransitioner


class StateMachineService:
    def __init__(
        self,
        state_transitioner: IStateTransitioner,
        api_action_caller: IApiActionCaller,
        api_sync: IApiSync,
    ) -> None:
        self._state_transitioner = state_transitioner
        self._api_action_caller = api_action_caller
        self._api_sync = api_sync

    def submit_review(self, records) -> None:
        self._state_transitioner.transition(
            records, "draft", "internal_review",
            "Отправить на проверку можно только черновик.",
        )

    def return_draft(self, records) -> None:
        self._state_transitioner.transition(
            records, "internal_review", "draft",
            "Вернуть в черновик можно только из внутренней проверки.",
        )

    def approve(self, records) -> None:
        self._state_transitioner.transition(
            records, "internal_review", "active",
            "Одобрить можно только объект на внутренней проверке.",
        )

    def send_to_mls(self, records) -> None:
        self._state_transitioner.transition(
            records, "active", "moderation",
            "Отправить в MLS можно только объект в продаже.",
        )
        for record in records:
            if record.external_id:
                self._api_action_caller.call_action(record, "resume")
            else:
                self._api_sync.push_property(record)

    def remove_from_mls(self, records) -> None:
        self._state_transitioner.transition(
            records,
            ("moderation", "legal_review", "published"),
            "active",
            "Убрать из MLS возможен только для объектов в MLS-процессе.",
        )

    def sell(self, records) -> None:
        self._state_transitioner.transition(
            records, ("active", "published"), "sold",
            "Отметить как проданный можно только объект в продаже или опубликованный.",
        )

    def unpublish(self, records) -> None:
        self._state_transitioner.transition(
            records, ("active", "published"), "unpublished",
            "Снять можно только объект в продаже или опубликованный.",
        )
        self._api_action_caller.call_action(records, "suspend")

    def republish(self, records) -> None:
        self._state_transitioner.transition(
            records, "unpublished", "active",
            "Вернуть в продажу можно только снятый с публикации объект.",
        )
        self._api_action_caller.call_action(records, "resume")

    def archive_property(self, records) -> None:
        self._state_transitioner.transition(
            records, "published", "archived",
            "Архивировать можно только опубликованный объект.",
        )

    def fix_rejected(self, records) -> None:
        self._state_transitioner.transition(
            records, "rejected", "internal_review",
            "Исправить можно только отклонённый объект.",
        )
