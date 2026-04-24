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

    def browse_snapshot(self, snapshot_id: int):
        return self._env["estate.market.snapshot"].browse(snapshot_id)

    def find_recent_samples(
        self,
        city_id: int,
        district_id: int | None,
        property_type: str,
        rooms: int | None,
        max_age_days: int,
        limit: int,
    ) -> list[tuple[int, list[float]]]:
        threshold = datetime.now() - timedelta(days=max_age_days)
        params: list[object] = [city_id, property_type, threshold]
        district_clause = (
            "district_id IS NULL"
            if district_id is None
            else "district_id = %s"
        )
        if district_id is not None:
            params.append(district_id)
        rooms_clause = "" if rooms is None else "AND rooms = %s"
        if rooms is not None:
            params.append(rooms)
        params.append(limit)

        query = f"""
            SELECT id, samples_per_sqm
            FROM estate_market_snapshot
            WHERE city_id = %s
              AND property_type = %s
              AND collected_at >= %s
              AND {district_clause}
              {rooms_clause}
              AND samples_per_sqm IS NOT NULL
              AND array_length(samples_per_sqm, 1) > 0
            ORDER BY collected_at DESC
            LIMIT %s
        """
        self._env.cr.execute(query, params)
        rows = self._env.cr.fetchall()
        return [(int(row[0]), list(row[1] or [])) for row in rows]
