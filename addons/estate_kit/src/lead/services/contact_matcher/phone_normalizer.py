class PhoneNormalizer:
    def normalize(self, phone: str | None) -> str:
        """Оставляет только цифры и нормализует 8 → 7 для KZ/RU номеров."""
        if not phone:
            return ""
        digits = "".join(c for c in phone if c.isdigit())
        if len(digits) == 11 and digits[0] == "8":
            digits = "7" + digits[1:]
        return digits
