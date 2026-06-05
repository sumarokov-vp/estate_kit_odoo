from .protocols import (
    IContactBuilder,
    IFeaturesCollector,
    IMetricsBuilder,
    ISectionsBuilder,
    IStateBadgeBuilder,
    ITypeLabelResolver,
)
from .public_card_data import PublicCardData


class PublicCardRendererService:
    def __init__(
        self,
        type_label_resolver: ITypeLabelResolver,
        state_badge_builder: IStateBadgeBuilder,
        metrics_builder: IMetricsBuilder,
        sections_builder: ISectionsBuilder,
        features_collector: IFeaturesCollector,
        contact_builder: IContactBuilder,
    ) -> None:
        self._type_label_resolver = type_label_resolver
        self._state_badge_builder = state_badge_builder
        self._metrics_builder = metrics_builder
        self._sections_builder = sections_builder
        self._features_collector = features_collector
        self._contact_builder = contact_builder

    def render(self, prop, token: str) -> PublicCardData:
        return PublicCardData(
            type_label=self._type_label_resolver.resolve(prop),
            state_badge=self._state_badge_builder.build(prop),
            metrics=self._metrics_builder.build(prop),
            sections=self._sections_builder.build(prop),
            features=self._features_collector.collect(prop),
            contact=self._contact_builder.build(prop, token),
        )
