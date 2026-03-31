from typing import Any, Callable

from .odoo_match_writer import OdooMatchWriter
from .service import MatchTransitionService
from .set_rejected import SetRejected
from .set_selected import SetSelected
from .set_viewed import SetViewed


class Factory:
    @staticmethod
    def create(env: Any, raw_write: Callable) -> MatchTransitionService:
        writer = OdooMatchWriter(raw_write)

        viewed_stage = env.ref("estate_kit.match_stage_viewed")
        rejected_stage = env.ref("estate_kit.match_stage_rejected")
        selected_stage = env.ref("estate_kit.match_stage_selected")
        negotiation_stage = env.ref("estate_kit.crm_stage_negotiation")

        return MatchTransitionService(
            set_viewed=SetViewed(writer, viewed_stage.id),
            set_rejected=SetRejected(writer, rejected_stage.id),
            set_selected=SetSelected(
                writer, selected_stage.id, rejected_stage.id, negotiation_stage.id,
            ),
        )
