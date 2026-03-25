class DeeplinkBuilderService:
    def __init__(self, bot_username: str) -> None:
        self._bot_username = bot_username

    def build(self, lead_code: str | None) -> str | bool:
        if self._bot_username and lead_code:
            return f"https://t.me/{self._bot_username}?start=lead_{lead_code}"
        return False
