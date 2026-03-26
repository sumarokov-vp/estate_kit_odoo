from ....shared.services.api_client import EstateKitApiClient
from .local_property_searcher import LocalPropertySearcher
from .mls_property_searcher import MlsPropertySearcher
from .service import UnifiedSearchService


class Factory:
    @staticmethod
    def create(env) -> UnifiedSearchService:
        api_client = EstateKitApiClient(env)
        local_searcher = LocalPropertySearcher(env)
        mls_searcher = MlsPropertySearcher(api_client)
        return UnifiedSearchService(local_searcher, mls_searcher)
