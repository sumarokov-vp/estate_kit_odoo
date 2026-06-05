from .protocols import IMainImageResolver


class ImageUrlResolver:
    def __init__(self, env, main_image_resolver: IMainImageResolver) -> None:
        self._env = env
        self._main_image_resolver = main_image_resolver

    def resolve(self, prop) -> str | None:
        image = self._main_image_resolver.resolve(prop)
        if not image:
            return None
        if not (image.image_key or image.thumbnail_key):
            return None
        token = (
            self._env["estate.property.public.view.token"]
            .sudo()
            .get_or_create_token(prop.id)
        )
        return f"/estate_kit/view/{token}/thumb/{image.id}"
