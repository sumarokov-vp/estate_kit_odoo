from typing import Any


class ActivityCreator:
    def __init__(self, env: Any) -> None:
        self._env = env

    def create(self, prop: Any, summary: str, note: str) -> None:
        responsible_user = prop.user_id or prop.listing_agent_id
        if not responsible_user:
            return
        activity_type = self._env.ref("mail.mail_activity_data_todo")
        self._env["mail.activity"].create({
            "activity_type_id": activity_type.id,
            "summary": summary,
            "note": note,
            "res_model_id": self._env["ir.model"]._get_id("estate.property"),
            "res_id": prop.id,
            "user_id": responsible_user.id,
        })
