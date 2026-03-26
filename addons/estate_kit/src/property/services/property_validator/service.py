from odoo.exceptions import ValidationError

from .protocols import IAddressFieldsValidator, IDuplicateChecker, IDuplicateOnWriteChecker, IStateTransitionChecker


class PropertyValidatorService:
    def __init__(
        self,
        duplicate_checker: IDuplicateChecker,
        duplicate_on_write_checker: IDuplicateOnWriteChecker,
        state_transition_checker: IStateTransitionChecker,
        address_fields_validator: IAddressFieldsValidator,
    ) -> None:
        self._checker = duplicate_checker
        self._duplicate_on_write_checker = duplicate_on_write_checker
        self._state_transition_checker = state_transition_checker
        self._address_fields_validator = address_fields_validator

    def validate_create(self, vals_list: list[dict], context: dict) -> None:
        if context.get("skip_duplicate_check"):
            return
        for vals in vals_list:
            if not context.get("allow_empty_address"):
                self._address_fields_validator.require_address_fields(vals)
            result = self._checker.check(vals)
            if result:
                raise ValidationError(result.message)

    def validate_write(self, records, vals: dict, context: dict) -> None:
        if not context.get("skip_duplicate_check"):
            self._duplicate_on_write_checker.check_duplicate_on_write(records, vals)
        if "state" in vals and not context.get("force_state_change"):
            self._state_transition_checker.check_state_transition(records, vals["state"])
