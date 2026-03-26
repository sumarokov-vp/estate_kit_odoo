from typing import Any

from odoo import fields


class EventCleaner:
    def __init__(self, env: Any) -> None:
        self._env = env

    def cleanup(self, retention_days: int) -> None:
        cutoff = fields.Datetime.subtract(fields.Datetime.now(), days=retention_days)
        self._env["estatekit.webhook.event"].sudo().search(
            [("processed_at", "<", cutoff)]
        ).unlink()
