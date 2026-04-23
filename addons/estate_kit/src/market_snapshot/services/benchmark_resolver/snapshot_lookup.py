from datetime import datetime, timedelta


class SnapshotLookup:
    def __init__(self, env) -> None:
        self._env = env

    def find_latest(
        self,
        city_id: int,
        district_id: int | None,
        property_type: str,
        rooms: int | None,
        max_age_days: int,
    ):
        threshold = datetime.now() - timedelta(days=max_age_days)
        domain = [
            ("city_id", "=", city_id),
            ("property_type", "=", property_type),
            ("collected_at", ">=", threshold),
        ]
        if district_id is None:
            domain.append(("district_id", "=", False))
        else:
            domain.append(("district_id", "=", district_id))
        if rooms is not None:
            domain.append(("rooms", "=", rooms))

        return self._env["estate.market.snapshot"].search(
            domain, order="collected_at desc", limit=1,
        )
