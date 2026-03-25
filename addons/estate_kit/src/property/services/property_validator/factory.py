from .....services.duplicate_checker import DuplicateChecker
from .service import PropertyValidatorService


class Factory:
    @staticmethod
    def create(env) -> PropertyValidatorService:
        checker = DuplicateChecker(env)
        return PropertyValidatorService(checker)
