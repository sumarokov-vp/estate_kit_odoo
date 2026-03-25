from odoo.exceptions import UserError

from .protocols import IApiClient, IApiSync


class StateMachineService:
    def __init__(self, api_client: IApiClient, api_sync: IApiSync, env) -> None:
        self._api_client = api_client
        self._api_sync = api_sync
        self._env = env

    def _transition(self, records, from_states: str | tuple, to_state: str, error_msg: str) -> None:
        if isinstance(from_states, str):
            from_states = (from_states,)
        for record in records:
            if record.state not in from_states:
                raise UserError(error_msg)
        records.with_context(force_state_change=True).write({"state": to_state})

    def _api_call_action(self, records, action: str) -> None:
        for record in records:
            if record.external_id and self._api_client.is_configured:
                self._api_client.post(f"/properties/{record.external_id}/{action}", {})

    def submit_review(self, records) -> None:
        self._transition(records, "draft", "internal_review", "Отправить на проверку можно только черновик.")

    def return_draft(self, records) -> None:
        self._transition(records, "internal_review", "draft", "Вернуть в черновик можно только из внутренней проверки.")

    def approve(self, records) -> None:
        self._transition(records, "internal_review", "active", "Одобрить можно только объект на внутренней проверке.")

    def send_to_mls(self, records) -> None:
        self._transition(records, "active", "moderation", "Отправить в MLS можно только объект в продаже.")
        for record in records:
            if record.external_id:
                self._api_call_action(record, "resume")
            else:
                self._api_sync.push_property(record)

    def remove_from_mls(self, records) -> None:
        self._transition(
            records,
            ("moderation", "legal_review", "published"),
            "active",
            "Убрать из MLS возможен только для объектов в MLS-процессе.",
        )

    def sell(self, records) -> None:
        self._transition(
            records,
            ("active", "published"),
            "sold",
            "Отметить как проданный можно только объект в продаже или опубликованный.",
        )

    def unpublish(self, records) -> None:
        self._transition(
            records,
            ("active", "published"),
            "unpublished",
            "Снять можно только объект в продаже или опубликованный.",
        )
        self._api_call_action(records, "suspend")

    def republish(self, records) -> None:
        self._transition(records, "unpublished", "active", "Вернуть в продажу можно только снятый с публикации объект.")
        self._api_call_action(records, "resume")

    def archive_property(self, records) -> None:
        self._transition(records, "published", "archived", "Архивировать можно только опубликованный объект.")

    def fix_rejected(self, records) -> None:
        self._transition(records, "rejected", "internal_review", "Исправить можно только отклонённый объект.")
