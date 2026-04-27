from .property_type_labels import PROPERTY_TYPE_LABELS


class NameBuilderService:
    def build(self, property_type: str | None, contact_name: str | None) -> str:
        type_label = PROPERTY_TYPE_LABELS.get(property_type or "", "")
        contact = (contact_name or "").strip()
        if type_label and contact:
            return f"{type_label} · {contact}"
        if type_label:
            return type_label
        return contact
