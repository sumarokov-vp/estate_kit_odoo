from typing import Any

from odoo import fields

from ..matching_client import MatchResult


class MatchRepository:
    def __init__(self, env: Any) -> None:
        self._env = env

    def sync(self, lead_id: int, results: list[MatchResult]) -> int:
        Match = self._env["estate.lead.match"]
        now = fields.Datetime.now()

        existing = {m.property_id.id: m for m in Match.search([("lead_id", "=", lead_id)])}
        result_ids = {r.property_id for r in results}

        to_unlink = [m.id for pid, m in existing.items() if pid not in result_ids]
        if to_unlink:
            Match.browse(to_unlink).unlink()

        for result in results:
            if result.property_id in existing:
                existing[result.property_id].write({"score": result.score, "match_date": now})
            else:
                prop = self._env["estate.property"].browse(result.property_id)
                if prop.exists():
                    Match.create(
                        {
                            "lead_id": lead_id,
                            "property_id": result.property_id,
                            "score": result.score,
                        }
                    )

        self._env["crm.lead"].browse(lead_id).write({"last_matching_date": now})
        return Match.search_count([("lead_id", "=", lead_id)])
