class TelHrefBuilder:
    def build(self, phone: str | None) -> str | None:
        if not phone:
            return None
        digits = "".join(ch for ch in phone if ch.isdigit())
        prefix = "+" if phone.strip().startswith("+") else ""
        return f"tel:{prefix}{digits}"
