from odoo.exceptions import UserError


class StateTransitioner:
    def transition(self, records, from_states: str | tuple, to_state: str, error_msg: str) -> None:
        if isinstance(from_states, str):
            from_states = (from_states,)
        for record in records:
            if record.state not in from_states:
                raise UserError(error_msg)
        records.with_context(force_state_change=True).write({"state": to_state})
