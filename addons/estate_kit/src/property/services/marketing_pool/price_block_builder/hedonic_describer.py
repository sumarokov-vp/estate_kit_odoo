from ..price_score_calculator.hedonic_factor import HedonicFactor
from .protocols import IMoneyFormatter


class HedonicDescriber:
    def __init__(self, money_formatter: IMoneyFormatter) -> None:
        self._money_formatter = money_formatter

    def describe(
        self,
        factors: list[HedonicFactor],
        multiplier: float,
        median_per_sqm: float,
        expected_per_sqm: float,
    ) -> list[str]:
        if not factors or multiplier == 1.0:
            return [
                "Ожидаемая цена = медиана (поправок нет): %s"
                % self._format_per_sqm(expected_per_sqm),
            ]
        lines = ["Гедонические поправки к медиане:"]
        for factor in factors:
            lines.append(
                " • %s ×%.2f" % (factor.reason, factor.multiplier),
            )
        lines.append(
            " → Ожидаемая цена: %s" % self._format_per_sqm(expected_per_sqm),
        )
        return lines

    def _format_per_sqm(self, value: float) -> str:
        return "%s/м²" % self._money_formatter.format(value)
