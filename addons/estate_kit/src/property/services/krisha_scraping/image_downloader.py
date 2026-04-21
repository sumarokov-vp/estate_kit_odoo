from .protocols import IHttpSession


class ImageDownloader:
    def __init__(self, session: IHttpSession) -> None:
        self._session = session

    def download(self, url: str) -> bytes | None:
        return self._session.get_bytes(url)
