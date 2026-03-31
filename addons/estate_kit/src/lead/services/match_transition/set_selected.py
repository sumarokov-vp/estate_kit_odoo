from typing import Any

from .protocols import IMatchWriter


class SetSelected:
    def __init__(
        self, writer: IMatchWriter, stage_id: int, rejected_stage_id: int,
        negotiation_stage_id: int,
    ) -> None:
        self._writer = writer
        self._stage_id = stage_id
        self._rejected_stage_id = rejected_stage_id
        self._negotiation_stage_id = negotiation_stage_id

    def execute(self, match: Any) -> None:
        lead = match.lead_id
        prev = lead.match_ids.filtered(
            lambda m, mid=match.id, sid=self._stage_id: (
                m.stage_id.id == sid and m.id != mid
            )
        )
        if prev:
            self._writer.write(prev, {"stage_id": self._rejected_stage_id})

        self._writer.write(match, {"stage_id": self._stage_id})
        lead.write({
            "property_id": match.property_id.id,
            "stage_id": self._negotiation_stage_id,
        })
