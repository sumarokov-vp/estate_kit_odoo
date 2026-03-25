from .protocols import IPhoneNormalizer


class PartnerSearcher:
    def __init__(self, env, normalizer: IPhoneNormalizer) -> None:
        self._env = env
        self._normalizer = normalizer

    def find_by_phone(self, phone: str | None) -> int | None:
        normalized = self._normalizer.normalize(phone)
        if not normalized:
            return None

        partners = self._env["res.partner"].search([
            "|",
            ("phone", "!=", False),
            ("mobile", "!=", False),
        ])
        for partner in partners:
            if self._normalizer.normalize(partner.phone) == normalized:
                return partner.id
            if self._normalizer.normalize(partner.mobile) == normalized:
                return partner.id
        return None
