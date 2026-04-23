from .config_param_reader import ConfigParamReader
from .config_provider import PriceScoreConfigProvider
from .deviation_calculator import DeviationCalculator
from .hedonic_multiplier_calculator import HedonicMultiplierCalculator
from .score_mapper import ScoreMapper
from .service import PriceScoreCalculator


class Factory:
    @staticmethod
    def create(env) -> PriceScoreCalculator:
        config = PriceScoreConfigProvider(ConfigParamReader(env)).load()
        return PriceScoreCalculator(
            hedonic_calculator=HedonicMultiplierCalculator(config.hedonic),
            deviation_calculator=DeviationCalculator(),
            score_mapper=ScoreMapper(config.deviation_buckets),
        )
