from .config import MatchingClientConfig
from .http_client import HttpClient
from .service import MatchingClientService


class Factory:
    @staticmethod
    def create(env) -> MatchingClientService:
        config = MatchingClientConfig.from_env(env)
        http_client = HttpClient(config.base_url)
        return MatchingClientService(http_client)
