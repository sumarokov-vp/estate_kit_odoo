from typing import Any

from .field_mapping import _COMMON_FIELDS, PROPERTY_TYPE_FIELDS


class ScoringMessageBuilder:
    def build(self, property_data: dict[str, Any]) -> str:
        prop_type = property_data.get("property_type", "apartment")
        type_fields = PROPERTY_TYPE_FIELDS.get(prop_type, PROPERTY_TYPE_FIELDS["apartment"])
        all_fields = _COMMON_FIELDS + type_fields

        lines: list[str] = []

        benchmark = property_data.get("market_benchmark")
        if benchmark:
            lines.append("Рыночный бенчмарк (срез с Krisha.kz):")
            lines.append(
                "- Срез: %s / %s / %s комнат: %s"
                % (
                    benchmark.get("city", ""),
                    benchmark.get("district") or "без района",
                    benchmark.get("rooms") or "все",
                    benchmark.get("relax_level", ""),
                )
            )
            lines.append(
                "- Медиана цены за м²: %.0f KZT"
                % benchmark.get("median_per_sqm", 0)
            )
            lines.append(
                "- P25–P75 за м²: %.0f – %.0f KZT"
                % (benchmark.get("p25_per_sqm", 0), benchmark.get("p75_per_sqm", 0))
            )
            lines.append(
                "- Размер выборки: %d объявлений" % benchmark.get("sample_size", 0)
            )
            lines.append(
                "- Дата снапшота: %s" % benchmark.get("collected_at", "")
            )
            lines.append("")

        price_eval = property_data.get("price_evaluation")
        if price_eval:
            lines.append("Оценка цены формулой:")
            lines.append(
                "- Фактическая цена за м²: %.0f KZT"
                % price_eval.get("actual_per_sqm", 0)
            )
            lines.append(
                "- Ожидаемая цена за м² (медиана × гедонические поправки): %.0f KZT"
                % price_eval.get("expected_per_sqm", 0)
            )
            lines.append(
                "- Отклонение: %+.1f%%" % (price_eval.get("deviation", 0) * 100)
            )
            lines.append(
                "- price_score (рассчитан формулой): %d"
                % price_eval.get("score", 0)
            )
            factors = price_eval.get("hedonic_factors_applied") or []
            if factors:
                lines.append("- Применённые поправки: %s" % ", ".join(factors))
            lines.append("")

        lines.append("Данные объекта недвижимости:")
        for key, label, optional in all_fields:
            value = property_data.get(key)
            if value:
                lines.append(f"- {label}: {value}")
            elif not optional:
                lines.append(f"- {label}: не указано")
        return "\n".join(lines)
