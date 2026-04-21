from .protocols import IHttpSession


class HttpFetcher:
    def __init__(self, session: IHttpSession) -> None:
        self._session = session

    def fetch(self, url: str) -> str:
        return self._session.get_text(url)
