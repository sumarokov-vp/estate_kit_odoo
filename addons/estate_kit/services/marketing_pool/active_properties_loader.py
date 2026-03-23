POOL_ELIGIBLE_STATES = ("active", "published")


class ActivePropertiesLoader:
    def __init__(self, env):
        self._env = env

    def load(self):
        return self._env["estate.property"].search([
            ("state", "in", list(POOL_ELIGIBLE_STATES)),
        ])
