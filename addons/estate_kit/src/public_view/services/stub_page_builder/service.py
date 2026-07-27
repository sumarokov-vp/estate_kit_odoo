from .protocols import IInvalidLinkStubPageBuilder, IPropertyStubPageBuilder
from .stub_page import StubPage


class StubPageBuilderService:
    def __init__(
        self,
        property_stub_page_builder: IPropertyStubPageBuilder,
        invalid_link_stub_page_builder: IInvalidLinkStubPageBuilder,
    ) -> None:
        self._property_stub_page_builder = property_stub_page_builder
        self._invalid_link_stub_page_builder = invalid_link_stub_page_builder

    def build_for_property(self, prop) -> StubPage | None:
        return self._property_stub_page_builder.build(prop)

    def build_for_invalid_link(self) -> StubPage:
        return self._invalid_link_stub_page_builder.build()
