from .bot_url_builder import BotUrlBuilder
from .contact_builder import ContactBuilder
from .features_collector import FeaturesCollector
from .metric_value_resolver import MetricValueResolver
from .metrics_builder import MetricsBuilder
from .phone_resolver import PhoneResolver
from .section_row_resolver import SectionRowResolver
from .sections_builder import SectionsBuilder
from .selection_labeler import SelectionLabeler
from .service import PublicCardRendererService
from .state_badge_builder import StateBadgeBuilder
from .tel_href_builder import TelHrefBuilder
from .type_label_resolver import TypeLabelResolver


class Factory:
    @staticmethod
    def create(env) -> PublicCardRendererService:
        selection_labeler = SelectionLabeler()
        contact_builder = ContactBuilder(
            phone_resolver=PhoneResolver(env),
            tel_href_builder=TelHrefBuilder(),
            bot_url_builder=BotUrlBuilder(env),
        )
        return PublicCardRendererService(
            type_label_resolver=TypeLabelResolver(selection_labeler),
            state_badge_builder=StateBadgeBuilder(),
            metrics_builder=MetricsBuilder(MetricValueResolver(selection_labeler)),
            sections_builder=SectionsBuilder(SectionRowResolver(selection_labeler)),
            features_collector=FeaturesCollector(),
            contact_builder=contact_builder,
        )
