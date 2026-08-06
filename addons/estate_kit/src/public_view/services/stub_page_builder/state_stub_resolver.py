from .stub_page import StubText
from .stub_texts import STATE_STUBS


class StateStubResolver:
    def resolve(self, prop) -> StubText | None:
        return STATE_STUBS.get(prop.state)
