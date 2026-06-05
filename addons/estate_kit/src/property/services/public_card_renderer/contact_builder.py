from .protocols import IBotUrlBuilder, IPhoneResolver, ITelHrefBuilder


class ContactBuilder:
    def __init__(
        self,
        phone_resolver: IPhoneResolver,
        tel_href_builder: ITelHrefBuilder,
        bot_url_builder: IBotUrlBuilder,
    ) -> None:
        self._phone_resolver = phone_resolver
        self._tel_href_builder = tel_href_builder
        self._bot_url_builder = bot_url_builder

    def build(self, prop, token: str) -> dict:
        phone = self._phone_resolver.resolve(prop)
        return {
            "name": prop.user_id.name or None,
            "phone": phone,
            "tel_href": self._tel_href_builder.build(phone),
            "bot_url": self._bot_url_builder.build(token),
        }
