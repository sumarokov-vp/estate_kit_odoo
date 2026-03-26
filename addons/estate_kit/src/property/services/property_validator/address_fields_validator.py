from odoo.exceptions import ValidationError

_REQUIRED_ADDRESS_FIELDS = ("city_id", "street_id", "house_number")


class AddressFieldsValidator:
    def require_address_fields(self, vals: dict) -> None:
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
