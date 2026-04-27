class PartnerCreator:
    def __init__(self, env) -> None:
        self._env = env

    def create(self, name: str, phone: str) -> int:
        partner = self._env["res.partner"].create({
            "name": name,
            "phone": phone,
        })
        return partner.id
