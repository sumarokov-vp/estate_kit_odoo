class ConfigParamReader:
    def __init__(self, env) -> None:
        self._env = env

    def read_float(self, key: str, default: float) -> float:
        raw = self._env["ir.config_parameter"].sudo().get_param(key)
        if raw in (False, None, ""):
            return default
        try:
            return float(raw)
        except (TypeError, ValueError):
            return default
