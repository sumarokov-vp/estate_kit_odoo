from .address_fields_validator import AddressFieldsValidator
from .duplicate_checker import DuplicateChecker
from .duplicate_on_write_checker import DuplicateOnWriteChecker
from .service import PropertyValidatorService
from .state_transition_checker import StateTransitionChecker


class Factory:
    @staticmethod
    def create(env) -> PropertyValidatorService:
        duplicate_checker = DuplicateChecker(env)
        duplicate_on_write_checker = DuplicateOnWriteChecker(duplicate_checker)
        state_transition_checker = StateTransitionChecker()
        address_fields_validator = AddressFieldsValidator()
        return PropertyValidatorService(
            duplicate_checker,
            duplicate_on_write_checker,
            state_transition_checker,
            address_fields_validator,
        )
