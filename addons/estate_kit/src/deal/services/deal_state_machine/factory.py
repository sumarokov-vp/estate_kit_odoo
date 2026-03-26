from .service import DealStateMachineService
from .state_transitioner import StateTransitioner


class Factory:
    @staticmethod
    def create(env) -> DealStateMachineService:
        state_transitioner = StateTransitioner()
        return DealStateMachineService(state_transitioner)
