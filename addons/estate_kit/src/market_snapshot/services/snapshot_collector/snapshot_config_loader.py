from .config import SnapshotCollectorConfig, SnapshotTarget


class SnapshotConfigLoader:
    def __init__(self, env, config: SnapshotCollectorConfig) -> None:
        self._env = env
        self._config = config

    def load(self) -> list[SnapshotTarget]:
        records = self._env["estate.market.snapshot.config"].search([
            ("active", "=", True),
        ])
        targets: list[SnapshotTarget] = []
        for rec in records:
            targets.append(
                SnapshotTarget(
                    config_id=rec.id,
                    city_id=rec.city_id.id,
                    city_name=rec.city_id.name,
                    district_id=rec.district_id.id if rec.district_id else None,
                    district_name=rec.district_id.name if rec.district_id else None,
                    property_type=rec.property_type,
                    rooms=rec.rooms or 0,
                    max_pages=rec.max_pages or self._config.default_max_pages,
                )
            )
        return targets
