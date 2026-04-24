from ..price_score_calculator.result import PriceScoreResult
from .protocols import (
    IBucketDescriber,
    IHedonicDescriber,
    IMoneyFormatter,
    INumberFormatter,
    IPriceScoreConfigProvider,
    ISliceDescriber,
)
from .result import PriceBlock


class PriceBlockBuilder:
    def __init__(
        self,
        money_formatter: IMoneyFormatter,
        number_formatter: INumberFormatter,
        slice_describer: ISliceDescriber,
        hedonic_describer: IHedonicDescriber,
        bucket_describer: IBucketDescriber,
        config_provider: IPriceScoreConfigProvider,
    ) -> None:
        self._money_formatter = money_formatter
        self._number_formatter = number_formatter
        self._slice_describer = slice_describer
        self._hedonic_describer = hedonic_describer
        self._bucket_describer = bucket_describer
        self._config_provider = config_provider

    def build(self, prop, benchmark, price_score_result: PriceScoreResult) -> PriceBlock:
        def money_per_sqm(value: float) -> str:
            return "%s/м²" % self._money_formatter.format(value)

        lines: list[str] = []
        lines.append("Цена: %d/10" % price_score_result.score)
        lines.append("")
        lines.append("Расчёт (формула, без AI):")

        lines.append(
            " • Ваша цена: %s (%s / %s м²)"
            % (
                money_per_sqm(price_score_result.actual_per_sqm),
                self._money_formatter.format(prop.price),
                self._number_formatter.format_integer(prop.area_total),
            )
        )
        lines.append(
            " • Медиана рынка: %s"
            % money_per_sqm(benchmark.median_price_per_sqm),
        )
        lines.append(
            " • Срез: %s"
            % self._slice_describer.describe_slice(
                benchmark.city_name,
                prop.property_type,
                benchmark.property_type,
            )
        )
        lines.append(
            " • Уровень данных: %s"
            % self._slice_describer.describe_relax(
                benchmark.relax_level,
                benchmark.district_name,
                benchmark.rooms,
            )
        )
        lines.append(
            " • Выборка: %d объявлений, снапшот от %s"
            % (
                benchmark.sample_size,
                benchmark.collected_at.strftime("%d.%m.%Y"),
            )
        )
        lines.append(
            " • P25–P75: %s – %s"
            % (
                money_per_sqm(benchmark.p25_price_per_sqm),
                money_per_sqm(benchmark.p75_price_per_sqm),
            )
        )
        lines.append("")

        hedonic_lines = self._hedonic_describer.describe(
            price_score_result.hedonic_factors_applied,
            price_score_result.hedonic_multiplier,
            benchmark.median_price_per_sqm,
            price_score_result.expected_per_sqm,
        )
        lines.extend(hedonic_lines)
        lines.append("")

        deviation_percent = price_score_result.deviation * 100
        bucket_text = self._bucket_describer.describe(
            price_score_result.bucket_applied,
            self._config_provider.get_buckets(),
        )
        lines.append(
            "Отклонение факт / ожидаемой: %s → bucket %s → оценка %d/10"
            % (
                self._number_formatter.format_percent_signed(deviation_percent),
                bucket_text,
                price_score_result.score,
            )
        )

        return PriceBlock(text="\n".join(lines), score=price_score_result.score)
