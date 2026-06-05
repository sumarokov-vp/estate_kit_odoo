from .metrics_layout import METRICS_BY_TYPE
from .protocols import IMetricValueResolver


class MetricsBuilder:
    def __init__(self, metric_value_resolver: IMetricValueResolver) -> None:
        self._metric_value_resolver = metric_value_resolver

    def build(self, prop) -> list[dict]:
        specs = METRICS_BY_TYPE.get(prop.property_type, [])
        metrics: list[dict] = []
        for spec in specs:
            value = self._metric_value_resolver.resolve(prop, spec)
            if value:
                metrics.append({"label": spec[1], "value": value})
        return metrics
