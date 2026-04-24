from ..price_score_calculator.config_param_reader import ConfigParamReader
from ..price_score_calculator.config_provider import PriceScoreConfigProvider
from .bucket_describer import BucketDescriber
from .config_provider import PriceScoreConfigProviderAdapter
from .hedonic_describer import HedonicDescriber
from .money_formatter import MoneyFormatter
from .number_formatter import NumberFormatter
from .property_type_label_resolver import PropertyTypeLabelResolver
from .service import PriceBlockBuilder
from .slice_describer import SliceDescriber


class Factory:
    @staticmethod
    def create(env) -> PriceBlockBuilder:
        number_formatter = NumberFormatter()
        money_formatter = MoneyFormatter(number_formatter)
        property_type_label_resolver = PropertyTypeLabelResolver()
        slice_describer = SliceDescriber(property_type_label_resolver)
        hedonic_describer = HedonicDescriber(money_formatter)
        bucket_describer = BucketDescriber(number_formatter)
        config_provider = PriceScoreConfigProviderAdapter(
            PriceScoreConfigProvider(ConfigParamReader(env)),
        )
        return PriceBlockBuilder(
            money_formatter=money_formatter,
            number_formatter=number_formatter,
            slice_describer=slice_describer,
            hedonic_describer=hedonic_describer,
            bucket_describer=bucket_describer,
            config_provider=config_provider,
        )
