from .stub_page import StubText

SOLD = StubText(
    kind="sold",
    title="Объект продан",
    message=(
        "Этот объект уже нашёл своего покупателя. "
        "Свяжитесь с агентом — подберём похожие варианты."
    ),
)

WITHDRAWN = StubText(
    kind="withdrawn",
    title="Объект снят с продажи",
    message=(
        "Объект временно снят с продажи. "
        "Свяжитесь с агентом — он расскажет о статусе и похожих предложениях."
    ),
)

INVALID_LINK = StubText(
    kind="invalid",
    title="Ссылка недействительна",
    message=(
        "Срок действия ссылки истёк или она была отозвана. "
        "Попросите у агента новую ссылку на объект."
    ),
)

STATE_STUBS = {
    "sold": SOLD,
    "mls_sold": SOLD,
    "unpublished": WITHDRAWN,
    "mls_removed": WITHDRAWN,
}
