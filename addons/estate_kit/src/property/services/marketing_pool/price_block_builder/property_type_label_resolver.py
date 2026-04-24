from .property_type_labels import PROPERTY_TYPE_LABELS


class PropertyTypeLabelResolver:
    def resolve(self, property_type: str) -> str:
        return PROPERTY_TYPE_LABELS.get(property_type, property_type)
