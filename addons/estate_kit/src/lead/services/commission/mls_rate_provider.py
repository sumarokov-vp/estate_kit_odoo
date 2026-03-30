from typing import Any


class MlsRateProvider:
    def get_rate(self, lead: Any) -> float | None:
        if not lead.property_id:
            return None
        mls_rate = lead.property_id.min_commission_percent
        return mls_rate if mls_rate else None
