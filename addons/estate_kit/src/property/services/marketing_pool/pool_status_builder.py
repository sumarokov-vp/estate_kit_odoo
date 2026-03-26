from .config import PoolScoreConfig


class PoolStatusBuilder:
    def __init__(self, config: PoolScoreConfig, pool_eligible_states: frozenset[str]):
        self._config = config
        self._pool_eligible_states = pool_eligible_states

    def build(self, prop, scoring) -> str:
        if prop.state not in self._pool_eligible_states:
            state_label = dict(prop._fields["state"].selection).get(prop.state, prop.state)
            return "⚪ Не участвует (статус: %s)" % state_label

        failed = []
        if scoring.price_score < self._config.min_price:
            failed.append("цена")
        if scoring.quality_score < self._config.min_quality:
            failed.append("качество")
        if scoring.listing_score < self._config.min_listing:
            failed.append("карточка")

        mps = prop.marketing_pool_score
        if failed:
            return "🔴 Не проходит в пул (ниже порога: %s)" % ", ".join(failed)
        if mps >= self._config.t_include:
            return "🟢 Проходит в пул (MPS: %.1f)" % mps
        if mps >= self._config.t_exclude:
            return "🟡 Пограничная зона (MPS: %.1f)" % mps
        return "🔴 Не проходит в пул (MPS: %.1f)" % mps
