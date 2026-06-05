from .protocols import ISectionRowResolver
from .sections_layout import SECTIONS


class SectionsBuilder:
    def __init__(self, section_row_resolver: ISectionRowResolver) -> None:
        self._section_row_resolver = section_row_resolver

    def build(self, prop) -> list[dict]:
        sections: list[dict] = []
        for spec in SECTIONS:
            allowed = spec["property_types"]
            if allowed is not None and prop.property_type not in allowed:
                continue
            rows: list[tuple[str, str]] = []
            for row_spec in spec["rows"]:
                row = self._section_row_resolver.resolve(prop, row_spec)
                if row:
                    rows.append(row)
            if rows:
                sections.append(
                    {"title": spec["title"], "icon": spec["icon"], "rows": rows}
                )
        return sections
