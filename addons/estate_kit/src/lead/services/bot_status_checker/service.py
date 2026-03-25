class BotStatusCheckerService:
    def is_connected(self, telegram_user_id: str | None) -> bool:
        return bool(telegram_user_id)
