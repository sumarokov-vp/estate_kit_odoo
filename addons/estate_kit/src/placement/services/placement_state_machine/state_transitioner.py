from odoo.exceptions import UserError


class PlacementStateTransitioner:
    def transition(
        self,
        records,
        valid_from_states: tuple[str, ...],
        to_state: str,
        error_msg: str,
    ) -> None:
        for rec in records:
            if rec.state not in valid_from_states:
                raise UserError(error_msg)
            rec.state = to_state
