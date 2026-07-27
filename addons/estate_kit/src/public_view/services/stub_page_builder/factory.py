from ....property.services.public_card_renderer.phone_resolver import PhoneResolver
from ....property.services.public_card_renderer.tel_href_builder import TelHrefBuilder
from .contact_builder import StubContactBuilder
from .invalid_link_stub_page_builder import InvalidLinkStubPageBuilder
from .property_stub_page_builder import PropertyStubPageBuilder
from .service import StubPageBuilderService
from .state_stub_resolver import StateStubResolver


class Factory:
    @staticmethod
    def create(env) -> StubPageBuilderService:
        contact_builder = StubContactBuilder(
            phone_resolver=PhoneResolver(env),
            tel_href_builder=TelHrefBuilder(),
        )
        return StubPageBuilderService(
            property_stub_page_builder=PropertyStubPageBuilder(
                state_stub_resolver=StateStubResolver(),
                contact_builder=contact_builder,
            ),
            invalid_link_stub_page_builder=InvalidLinkStubPageBuilder(),
        )
