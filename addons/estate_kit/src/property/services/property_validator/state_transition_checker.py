from odoo.exceptions import UserError

from ..state_machine.transitions import ALLOWED_TRANSITIONS


class StateTransitionChecker:
    def check_state_transition(self, records, new_state: str) -> None:
        for record in records:
            allowed = ALLOWED_TRANSITIONS.get(record.state, [])
            if new_state not in allowed:
                raise UserError(
                    f"Переход из «{record.state}» в «{new_state}» не разрешён. "
                    "Используйте соответствующую кнопку действия."
                )
