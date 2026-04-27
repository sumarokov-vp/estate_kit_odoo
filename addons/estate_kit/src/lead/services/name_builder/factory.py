from .service import NameBuilderService


class Factory:
    @staticmethod
    def create() -> NameBuilderService:
        return NameBuilderService()
