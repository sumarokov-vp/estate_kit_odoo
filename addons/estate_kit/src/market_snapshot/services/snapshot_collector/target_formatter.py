from .config import SnapshotTarget


class TargetFormatter:
    def format(self, target: SnapshotTarget) -> str:
        parts = [target.city_name]
        if target.district_name:
            parts.append(target.district_name)
        parts.append(target.property_type)
        if target.rooms:
            parts.append("%d-комн." % target.rooms)
        return " / ".join(parts)
