from .config import HedonicCoefficients, PriceScoreConfig
from .protocols import IConfigParamReader

_NAMESPACE = "estate_kit.hedonic"


class PriceScoreConfigProvider:
    def __init__(self, reader: IConfigParamReader) -> None:
        self._reader = reader

    def load(self) -> PriceScoreConfig:
        defaults = HedonicCoefficients()

        condition_multipliers = {
            key: self._reader.read_float(
                "%s.condition_%s_adj" % (_NAMESPACE, key),
                default_value,
            )
            for key, default_value in defaults.condition_multipliers.items()
        }

        hedonic = HedonicCoefficients(
            first_floor_penalty=self._reader.read_float(
                "%s.first_floor_penalty" % _NAMESPACE,
                defaults.first_floor_penalty,
            ),
            last_floor_penalty=self._reader.read_float(
                "%s.last_floor_penalty" % _NAMESPACE,
                defaults.last_floor_penalty,
            ),
            parking_bonus=self._reader.read_float(
                "%s.parking_bonus" % _NAMESPACE,
                defaults.parking_bonus,
            ),
            year_built_penalty_per_decade=self._reader.read_float(
                "%s.year_built_penalty_per_decade" % _NAMESPACE,
                defaults.year_built_penalty_per_decade,
            ),
            year_built_reference=int(self._reader.read_float(
                "%s.year_built_reference" % _NAMESPACE,
                float(defaults.year_built_reference),
            )),
            condition_multipliers=condition_multipliers,
        )
        return PriceScoreConfig(hedonic=hedonic)
