class SpecsFormatter:
    def format(self, prop) -> str:
        parts = []
        if prop.area_total:
            parts.append(f"{prop.area_total:g} м²")
        if prop.rooms:
            parts.append(f"{prop.rooms} комн.")
        return " • ".join(parts)
