from .protocols import IBaseUrlProvider


class UrlBuilderService:
    def __init__(self, base_url_provider: IBaseUrlProvider) -> None:
        self._base_url_provider = base_url_provider

    def build(self, path: str) -> str:
        base_url = self._base_url_provider.get()
        suffix = path if path.startswith("/") else f"/{path}"
        return f"{base_url}{suffix}"

    def upload_url(self, token: str) -> str:
        return self.build(f"/estate_kit/upload/{token}")

    def public_view_url(self, token: str) -> str:
        return self.build(f"/estate_kit/view/{token}")
