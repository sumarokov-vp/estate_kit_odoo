from .config import KrishaImportConfig


class ConfigProvider:
    def __init__(self, env) -> None:
        self._env = env

    def load(self) -> KrishaImportConfig:
        params = self._env["ir.config_parameter"].sudo()
        search_url = params.get_param("estate_kit.krisha_search_url", "") or ""
        limit_raw = params.get_param("estate_kit.krisha_import_limit", "10") or "10"
        limit = int(limit_raw) if str(limit_raw).isdigit() else 10
        return KrishaImportConfig(search_url=search_url.strip(), limit=limit)
