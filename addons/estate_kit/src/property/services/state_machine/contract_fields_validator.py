from odoo.exceptions import UserError

REQUIRED_FIELDS = (
    ("contract_type", "Тип договора"),
    ("contract_number", "Номер договора"),
    ("contract_start", "Начало договора"),
    ("contract_end", "Окончание договора"),
)


class ContractFieldsValidator:
    def validate(self, records) -> None:
        for record in records:
            missing = [label for name, label in REQUIRED_FIELDS if not record[name]]
            if missing:
                raise UserError(
                    "Заполните поля договора перед одобрением: " + ", ".join(missing) + "."
                )
