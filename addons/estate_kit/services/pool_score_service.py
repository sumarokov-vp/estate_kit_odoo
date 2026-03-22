import logging
from datetime import timedelta
from typing import Any

from odoo import fields
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

POOL_INACTIVE_STATES = ("sold", "unpublished", "archived", "mls_sold", "mls_removed")


class PoolScoreService:
    def __init__(self, env: Any):
        self.env = env

    def calculate_all(self) -> None:
        """Calculate marketing_pool_score for all active properties."""
        Log = self.env["estate.kit.log"]
        CAT = "marketing_pool"
        Property = self.env["estate.property"]

        all_states = list(dict(Property._fields["state"].selection))
        active_states = [s for s in all_states if s not in POOL_INACTIVE_STATES]
        properties = Property.search([("state", "in", active_states)])
        if not properties:
            Log.log(CAT, "Нет активных объектов для расчёта", level="warning")
            return

        get_param = self.env["ir.config_parameter"].sudo().get_param
        w_scoring = float(get_param("estate_kit.pool_scoring_weight", "0.6"))
        w_tier = float(get_param("estate_kit.pool_tier_weight", "0.4"))
        t_include = float(get_param("estate_kit.pool_inclusion_threshold", "7.0"))
        t_exclude = float(get_param("estate_kit.pool_exclusion_threshold", "4.0"))
        min_price = int(get_param("estate_kit.pool_min_price_score", "3"))
        min_quality = int(get_param("estate_kit.pool_min_quality_score", "3"))
        min_listing = int(get_param("estate_kit.pool_min_listing_score", "3"))

        Log.log(
            CAT,
            "Расчёт пула запущен: %d объектов" % len(properties),
            details="W_scoring=%.2f, W_tier=%.2f, "
                    "мин. price=%d, мин. quality=%d, мин. listing=%d, "
                    "порог включения=%.1f, порог исключения=%.1f"
                    % (w_scoring, w_tier, min_price, min_quality, min_listing, t_include, t_exclude),
        )
        self.env.cr.commit()

        self._ensure_fresh_scoring(properties)

        now_str = fields.Datetime.now().strftime("%d.%m.%Y %H:%M")

        stats = {
            "total": len(properties),
            "no_scoring": 0,
            "below_price": 0,
            "below_quality": 0,
            "below_listing": 0,
            "below_inclusion": 0,
            "eligible": 0,
        }
        details_lines = []

        for prop in properties:
            latest = prop.scoring_ids[:1]
            if not latest:
                prop.write({
                    "marketing_pool_score": 0.0,
                    "marketing_pool_score_display": "— нет скоринга",
                })
                stats["no_scoring"] += 1
                continue

            avg_ai = (
                latest.price_score + latest.quality_score + latest.listing_score
            ) / 3.0
            tier_bonus = self.calc_tier_bonus(prop)
            mps = avg_ai * w_scoring + tier_bonus * w_tier

            if mps >= t_include:
                indicator = "🟢"
            elif mps >= t_exclude:
                indicator = "🟡"
            else:
                indicator = "🔴"

            prop.write({
                "marketing_pool_score": round(mps, 1),
                "marketing_pool_score_display": "%s %.1f (%s)" % (indicator, mps, now_str),
            })

            failed_scores = []
            if latest.price_score < min_price:
                failed_scores.append("price=%d<%d" % (latest.price_score, min_price))
            if latest.quality_score < min_quality:
                failed_scores.append("quality=%d<%d" % (latest.quality_score, min_quality))
            if latest.listing_score < min_listing:
                failed_scores.append("listing=%d<%d" % (latest.listing_score, min_listing))

            if failed_scores:
                if latest.price_score < min_price:
                    stats["below_price"] += 1
                if latest.quality_score < min_quality:
                    stats["below_quality"] += 1
                if latest.listing_score < min_listing:
                    stats["below_listing"] += 1
                details_lines.append(
                    "%s: %s (отклонён по порогу)" % (prop.name, ", ".join(failed_scores))
                )
            elif mps < t_include:
                stats["below_inclusion"] += 1
                details_lines.append(
                    "%s: MPS=%.1f < порог=%.1f (не включён)" % (prop.name, mps, t_include)
                )
            else:
                stats["eligible"] += 1
                details_lines.append(
                    "%s: MPS=%.1f ✓ (кандидат в пул)" % (prop.name, mps)
                )

        Log.log(
            CAT,
            "MPS рассчитан: %d объектов" % len(properties),
        )
        self.env.cr.commit()

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
        self.env.cr.commit()
        _logger.info("Marketing Pool Score: %s", summary)

    def update_single(self, prop) -> None:
        """Recalculate MPS for a single property after scoring."""
        latest = prop.scoring_ids[:1]
        if not latest:
            return

        get_param = self.env["ir.config_parameter"].sudo().get_param
        w_scoring = float(get_param("estate_kit.pool_scoring_weight", "0.6"))
        w_tier = float(get_param("estate_kit.pool_tier_weight", "0.4"))
        t_include = float(get_param("estate_kit.pool_inclusion_threshold", "7.0"))
        t_exclude = float(get_param("estate_kit.pool_exclusion_threshold", "4.0"))

        avg_ai = (latest.price_score + latest.quality_score + latest.listing_score) / 3.0
        tier_bonus = self.calc_tier_bonus(prop)
        mps = avg_ai * w_scoring + tier_bonus * w_tier

        if mps >= t_include:
            indicator = "🟢"
        elif mps >= t_exclude:
            indicator = "🟡"
        else:
            indicator = "🔴"

        now_str = fields.Datetime.now().strftime("%d.%m.%Y %H:%M")
        prop.write({
            "marketing_pool_score": round(mps, 1),
            "marketing_pool_score_display": "%s %.1f (%s)" % (indicator, mps, now_str),
        })

    def calc_tier_bonus(self, prop) -> float:
        """Calculate tier bonus for a property based on tier lists."""
        tiers = prop.tier_ids
        if not tiers:
            return 0.0

        has_agent = any(t.role == "listing_agent" for t in tiers)
        has_lead = any(t.role == "team_lead" for t in tiers)

        if has_agent and has_lead:
            base_bonus = 8.0
        elif has_lead:
            base_bonus = 6.0
        elif has_agent:
            base_bonus = 4.0
        else:
            return 0.0

        best_tier = min(tiers, key=lambda t: t.priority)
        role = best_tier.role
        same_role_tiers = self.env["estate.property.tier"].search_count([
            ("user_id", "=", best_tier.user_id.id),
            ("role", "=", role),
        ])
        p_max = max(same_role_tiers, 1)
        multiplier = 1.0 + (1 - best_tier.priority / p_max) * 0.25
        result = base_bonus * multiplier
        return min(max(result, 0.0), 10.0)

    def scores_below_threshold(self, scoring, min_price: int, min_quality: int, min_listing: int) -> bool:
        """Check if any individual score is below its threshold."""
        return (
            scoring.price_score < min_price
            or scoring.quality_score < min_quality
            or scoring.listing_score < min_listing
        )

    def _ensure_fresh_scoring(self, properties) -> None:
        """Score properties that have no AI scoring or scoring older than 14 days."""
        Log = self.env["estate.kit.log"]
        CAT = "marketing_pool"
        Scoring = self.env["estate.property.scoring"]
        cutoff = fields.Datetime.now() - timedelta(days=14)

        to_score = self.env["estate.property"]
        fresh_count = 0
        for prop in properties:
            latest = prop.scoring_ids[:1]
            if not latest or latest.scored_at < cutoff:
                to_score |= prop
            else:
                fresh_count += 1

        Log.log(
            CAT,
            "AI-скоринг: %d свежих, %d требуют расчёта" % (fresh_count, len(to_score)),
        )
        self.env.cr.commit()

        if not to_score:
            return

        scored = 0
        failed = 0
        for prop in to_score:
            try:
                Scoring.score_property(prop.id)
                scored += 1
            except UserError:
                failed += 1
                _logger.warning("Failed to score property %s, skipping", prop.id)
            self.env.cr.commit()

        Log.log(
            CAT,
            "AI-скоринг завершён: %d рассчитано, %d ошибок" % (scored, failed),
            level="warning" if failed else "info",
        )
        self.env.cr.commit()
