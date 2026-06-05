class BotUrlBuilder:
    def __init__(self, env) -> None:
        self._env = env

    def build(self, token: str) -> str | None:
        username = (
            self._env["ir.config_parameter"]
            .sudo()
            .get_param("estate_kit.customer_bot_username")
        )
        if not username:
            return None
        return f"https://t.me/{username}?start=property_{token}"
