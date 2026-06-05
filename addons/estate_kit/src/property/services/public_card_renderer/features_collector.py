from .features_layout import FEATURE_BOOLEANS


class FeaturesCollector:
    def collect(self, prop) -> list[str]:
        features = [
            label for field, label in FEATURE_BOOLEANS if getattr(prop, field, False)
        ]
        features.extend(e.name for e in prop.climate_equipment_ids)
        features.extend(a.name for a in prop.appliance_ids)
        features.extend(t.name for t in prop.tag_ids)
        return features
