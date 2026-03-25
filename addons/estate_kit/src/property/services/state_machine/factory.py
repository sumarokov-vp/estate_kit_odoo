from .....services.api_client import EstateKitApiClient
from ..api_sync import Factory as ApiSyncFactory
from .service import StateMachineService


class Factory:
    @staticmethod
    def create(env) -> StateMachineService:
        api_client = EstateKitApiClient(env)
        api_sync = ApiSyncFactory.create(env)
        return StateMachineService(api_client, api_sync, env)
