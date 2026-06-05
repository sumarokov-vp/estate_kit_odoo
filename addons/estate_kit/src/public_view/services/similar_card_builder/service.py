from .protocols import ICardBuilder


class SimilarCardBuilderService:
    def __init__(self, card_builder: ICardBuilder) -> None:
        self._card_builder = card_builder

    def build(self, properties) -> list[dict]:
        return [self._card_builder.build(prop) for prop in properties]
