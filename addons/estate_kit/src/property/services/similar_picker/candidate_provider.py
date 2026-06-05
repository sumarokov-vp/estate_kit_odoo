from .config import ACTIVE_STATES


class CandidateProvider:
    def __init__(self, env) -> None:
        self._env = env

    def find(self, prop):
        if not prop.city_id:
            return self._env["estate.property"].browse()
        return self._env["estate.property"].sudo().search(
            [
                ("id", "!=", prop.id),
                ("property_type", "=", prop.property_type),
                ("city_id", "=", prop.city_id.id),
                ("state", "in", list(ACTIVE_STATES)),
            ]
        )
