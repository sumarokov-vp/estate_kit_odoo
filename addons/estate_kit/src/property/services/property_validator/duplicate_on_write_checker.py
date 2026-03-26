from odoo.exceptions import ValidationError

from .duplicate_checker import ADDRESS_FIELDS, DuplicateChecker


class DuplicateOnWriteChecker:
    def __init__(self, duplicate_checker: DuplicateChecker) -> None:
        self._checker = duplicate_checker

    def check_duplicate_on_write(self, records, vals: dict) -> None:
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
