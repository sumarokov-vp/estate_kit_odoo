class SettingsRateProvider:
    def __init__(self, env) -> None:
        self._env = env

    def get_rate(self, lead) -> float:
        config = self._env["ir.config_parameter"].sudo()
        value = config.get_param("estate_kit.min_commission_percent", "0")
        return float(value)
