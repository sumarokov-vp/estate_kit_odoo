from .protocols import IContactBuilder, IStateStubResolver
from .stub_page import StubPage


class PropertyStubPageBuilder:
    def __init__(
        self,
        state_stub_resolver: IStateStubResolver,
        contact_builder: IContactBuilder,
    ) -> None:
        self._state_stub_resolver = state_stub_resolver
        self._contact_builder = contact_builder

    def build(self, prop) -> StubPage | None:
        text = self._state_stub_resolver.resolve(prop)
        if not text:
            return None
        return StubPage(
            kind=text.kind,
            title=text.title,
            message=text.message,
            contact=self._contact_builder.build(prop),
        )
