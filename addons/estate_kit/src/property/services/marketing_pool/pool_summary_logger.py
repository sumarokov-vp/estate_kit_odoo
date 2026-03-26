import logging

_logger = logging.getLogger(__name__)


class PoolSummaryLogger:
    def __init__(self, env):
        self._env = env

    def log(self, stats: dict, details_lines: list[str]) -> None:
        Log = self._env["estate.kit.log"]
        CAT = "marketing_pool"

        Log.log(
            CAT,
            "MPS рассчитан: %d объектов" % stats["total"],
        )
        self._env.cr.commit()

        summary = (
            "Итог: %d обработано, %d в пул, %d ниже MPS-порога, %d без скоринга. "
            "Отклонено по AI-порогам: price=%d, quality=%d, listing=%d"
            % (
                stats["total"],
                stats["eligible"],
                stats["below_inclusion"],
                stats["no_scoring"],
                stats["below_price"],
                stats["below_quality"],
                stats["below_listing"],
            )
        )
        Log.log(CAT, summary, details="\n".join(details_lines))
        self._env.cr.commit()
        _logger.info("Marketing Pool Score: %s", summary)
