from ....shared.services.api_client import EstateKitApiClient
from ..api_sync import Factory as ApiSyncFactory
from .api_action_caller import ApiActionCaller
from .service import StateMachineService
from .state_transitioner import StateTransitioner


class Factory:
    @staticmethod
    def create(env) -> StateMachineService:
        api_client = EstateKitApiClient(env)
        api_sync = ApiSyncFactory.create(env)
        state_transitioner = StateTransitioner()
        api_action_caller = ApiActionCaller(api_client)
        return StateMachineService(state_transitioner, api_action_caller, api_sync)
