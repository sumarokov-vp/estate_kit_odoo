from .stub_page import StubText
from .stub_texts import PENDING, PUBLIC_STATES, STATE_STUBS


class StateStubResolver:
    def resolve(self, prop) -> StubText | None:
        if prop.state in PUBLIC_STATES:
            return None
        return STATE_STUBS.get(prop.state, PENDING)
