from .....services.api_client import EstateKitApiClient
from .service import UnifiedSearchService


class Factory:
    @staticmethod
    def create(env) -> UnifiedSearchService:
        api_client = EstateKitApiClient(env)
        return UnifiedSearchService(api_client, env)
