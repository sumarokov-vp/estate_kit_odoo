from typing import cast


class SelectionLabeler:
    def label(self, prop, field_name: str) -> str | None:
        value = getattr(prop, field_name, False)
        if not value:
            return None
        key = cast(str, value)
        selection = prop._fields[field_name].selection
        if callable(selection):
            selection = selection(prop)
        items = cast(list[tuple[str, str]], selection)
        return dict(items).get(key)
