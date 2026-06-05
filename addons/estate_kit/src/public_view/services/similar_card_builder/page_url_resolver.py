class PageUrlResolver:
    def __init__(self, env) -> None:
        self._env = env

    def resolve(self, prop) -> str:
        return (
            self._env["estate.property.public.view.token"]
            .sudo()
            .get_or_create_url(prop.id)
        )
