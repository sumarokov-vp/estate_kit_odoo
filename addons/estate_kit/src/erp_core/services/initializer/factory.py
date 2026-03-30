from .initializer import Initializer


class Factory:
    @staticmethod
    def create() -> Initializer:
        return Initializer()
