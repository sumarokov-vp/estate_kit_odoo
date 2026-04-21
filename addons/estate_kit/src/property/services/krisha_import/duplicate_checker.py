class DuplicateChecker:
    def __init__(self, env) -> None:
        self._env = env

    def is_imported(self, krisha_url: str) -> bool:
        if not krisha_url:
            return False
        return bool(
            self._env["estate.property"]
            .with_context(active_test=False)
            .search_count([("krisha_url", "=", krisha_url)], limit=1)
        )
