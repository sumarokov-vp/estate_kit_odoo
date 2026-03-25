from __future__ import annotations

from typing import TYPE_CHECKING

from odoo.exceptions import UserError, ValidationError

from ..state_machine.transitions import ALLOWED_TRANSITIONS

if TYPE_CHECKING:
    from .....services.duplicate_checker import DuplicateChecker

_REQUIRED_ADDRESS_FIELDS = ("city_id", "street_id", "house_number")


class PropertyValidatorService:
    def __init__(self, duplicate_checker: DuplicateChecker) -> None:
        self._checker = duplicate_checker

    def validate_create(self, vals_list: list[dict], context: dict) -> None:
        if context.get("skip_duplicate_check"):
            return
        for vals in vals_list:
            if not context.get("allow_empty_address"):
                self._require_address_fields(vals)
            result = self._checker.check(vals)
            if result:
                raise ValidationError(result.message)

    def validate_write(self, records, vals: dict, context: dict) -> None:
        if not context.get("skip_duplicate_check"):
            self._check_duplicate_on_write(records, vals)
        if "state" in vals and not context.get("force_state_change"):
            self._check_state_transition(records, vals["state"])

    def _check_duplicate_on_write(self, records, vals: dict) -> None:
        from .....services.duplicate_checker import ADDRESS_FIELDS

        if not (ADDRESS_FIELDS & set(vals)):
            return
        for record in records:
            merged = {
                "city_id": vals.get("city_id", record.city_id.id),
                "street_id": vals.get("street_id", record.street_id.id),
                "house_number": vals.get("house_number", record.house_number),
                "apartment_number": vals.get("apartment_number", record.apartment_number),
                "property_type": vals.get("property_type", record.property_type),
                "deal_type": vals.get("deal_type", record.deal_type),
            }
            result = self._checker.check(merged, exclude_id=record.id)
            if result:
                raise ValidationError(result.message)

    @staticmethod
    def _check_state_transition(records, new_state: str) -> None:
        for record in records:
            allowed = ALLOWED_TRANSITIONS.get(record.state, [])
            if new_state not in allowed:
                raise UserError(
                    f"Переход из «{record.state}» в «{new_state}» не разрешён. "
                    "Используйте соответствующую кнопку действия."
                )

    @staticmethod
    def _require_address_fields(vals: dict) -> None:
        missing = []
        for field in _REQUIRED_ADDRESS_FIELDS:
            if not vals.get(field):
                missing.append(field)
        if vals.get("property_type") == "apartment" and not vals.get("apartment_number"):
            missing.append("apartment_number")
        if missing:
            raise ValidationError(
                f"Для создания объекта обязательны адресные поля: {', '.join(missing)}"
            )
