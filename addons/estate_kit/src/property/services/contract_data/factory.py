from .service import ContractDataService


class Factory:
    @staticmethod
    def create(env) -> ContractDataService:
        return ContractDataService(env)
