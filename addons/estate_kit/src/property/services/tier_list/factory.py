from .service import TierListService


class Factory:
    @staticmethod
    def create(env) -> TierListService:
        return TierListService(env)
