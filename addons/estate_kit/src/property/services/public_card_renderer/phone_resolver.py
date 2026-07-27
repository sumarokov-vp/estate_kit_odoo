class PhoneResolver:
    def __init__(self, env) -> None:
        self._env = env

    def resolve(self, prop) -> str | None:
        partner = prop.user_id.partner_id
        phone = partner.phone
        if not phone:
            company = self._env["res.company"].sudo().search([], limit=1)
            phone = company.phone or None
        return phone or None
