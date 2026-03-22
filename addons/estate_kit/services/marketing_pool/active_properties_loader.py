POOL_INACTIVE_STATES = ("sold", "unpublished", "archived", "mls_sold", "mls_removed")


class ActivePropertiesLoader:
    def __init__(self, env):
        self._env = env

    def load(self):
        Property = self._env["estate.property"]
        all_states = list(dict(Property._fields["state"].selection))
        active_states = [s for s in all_states if s not in POOL_INACTIVE_STATES]
        return Property.search([("state", "in", active_states)])
