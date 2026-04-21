class ConfigBaseUrlProvider:
    def __init__(self, env) -> None:
        self._env = env

    def get(self) -> str:
        value = (
            self._env["ir.config_parameter"].sudo().get_param("web.base.url") or ""
        )
        return value.rstrip("/")
