import logging
from dataclasses import dataclass

_logger = logging.getLogger(__name__)

# Типы, для которых apartment_number входит в ключ дубликата
_APARTMENT_TYPES = {"apartment"}

# Поля адреса, при изменении которых нужно перепроверять дубликаты
ADDRESS_FIELDS = {"city_id", "street_id", "house_number", "apartment_number", "property_type", "deal_type"}


@dataclass
class DuplicateCheckResult:
    """Результат одной ступени проверки."""
    check_name: str
    duplicate_id: int
    message: str


class DuplicateChecker:
    """Pipeline проверки дубликатов."""

    def __init__(self, env):
        self.env = env
        self.checks = [
            self._check_address,
        ]

    def check(self, vals: dict, exclude_id: int = 0) -> DuplicateCheckResult | None:
        """Последовательно проверяет все ступени, возвращает первый найденный дубликат."""
        for check_fn in self.checks:
            result = check_fn(vals, exclude_id)
            if result:
                return result
        return None

    def _check_address(self, vals: dict, exclude_id: int = 0) -> DuplicateCheckResult | None:
        """Проверка по адресу.

        Для квартир: city_id + street_id + house_number + apartment_number + property_type + deal_type
        Для остальных: city_id + street_id + house_number + property_type + deal_type
        """
        city_id = vals.get("city_id")
        street_id = vals.get("street_id")
        house_number = vals.get("house_number")
        property_type = vals.get("property_type")
        deal_type = vals.get("deal_type")

        if not all([city_id, street_id, house_number]):
            return None

        domain = [
            ("city_id", "=", city_id),
            ("street_id", "=", street_id),
            ("house_number", "=", house_number),
            ("property_type", "=", property_type),
            ("deal_type", "=", deal_type),
        ]

        if property_type in _APARTMENT_TYPES:
            apartment_number = vals.get("apartment_number")
            if apartment_number:
                domain.append(("apartment_number", "=", apartment_number))
            else:
                return None  # квартира без номера — не проверяем

        if exclude_id:
            domain.append(("id", "!=", exclude_id))

        duplicate = self.env["estate.property"].search(domain, limit=1)
        if not duplicate:
            return None

        return DuplicateCheckResult(
            check_name="address",
            duplicate_id=duplicate.id,
            message=f"Объект с таким адресом уже существует (ID: {duplicate.id}, «{duplicate.name}»)",
        )
