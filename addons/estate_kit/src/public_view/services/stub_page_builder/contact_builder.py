from .protocols import IPhoneResolver, ITelHrefBuilder


class StubContactBuilder:
    def __init__(
        self,
        phone_resolver: IPhoneResolver,
        tel_href_builder: ITelHrefBuilder,
    ) -> None:
        self._phone_resolver = phone_resolver
        self._tel_href_builder = tel_href_builder

    def build(self, prop) -> dict:
        phone = self._phone_resolver.resolve(prop)
        return {
            "name": prop.user_id.name or None,
            "phone": phone,
            "tel_href": self._tel_href_builder.build(phone),
        }
