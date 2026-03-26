from .service import PlacementStateMachineService
from .state_transitioner import PlacementStateTransitioner


class Factory:
    @staticmethod
    def create(env) -> PlacementStateMachineService:
        return PlacementStateMachineService(
            transitioner=PlacementStateTransitioner(),
        )
