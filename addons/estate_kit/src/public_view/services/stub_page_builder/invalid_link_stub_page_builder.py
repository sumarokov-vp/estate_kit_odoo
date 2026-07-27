from .stub_page import StubPage
from .stub_texts import INVALID_LINK


class InvalidLinkStubPageBuilder:
    def build(self) -> StubPage:
        return StubPage(
            kind=INVALID_LINK.kind,
            title=INVALID_LINK.title,
            message=INVALID_LINK.message,
            contact={},
        )
