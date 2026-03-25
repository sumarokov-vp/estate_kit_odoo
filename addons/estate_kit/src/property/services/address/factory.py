from .service import AddressService


class Factory:
    @staticmethod
    def create(env) -> AddressService:
        return AddressService(env)
