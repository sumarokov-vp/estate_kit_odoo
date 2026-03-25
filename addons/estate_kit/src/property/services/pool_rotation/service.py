import logging

from .protocols import IMarketingPool

_logger = logging.getLogger(__name__)

POOL_ELIGIBLE_STATES = ("active", "published")


class PoolRotationService:
    def __init__(self, marketing_pool: IMarketingPool, env) -> None:
        self._marketing_pool = marketing_pool
        self._env = env

    def rotate_pool(self) -> None:
        pool_tag = self._env.ref(
            "estate_kit.property_tag_marketing_pool", raise_if_not_found=False
        )
        if not pool_tag:
            _logger.warning("Marketing pool tag not found, skipping rotation.")
            return

        get_param = self._env["ir.config_parameter"].sudo().get_param
        min_price = int(get_param("estate_kit.pool_min_price_score", "3"))
        min_quality = int(get_param("estate_kit.pool_min_quality_score", "3"))
        min_listing = int(get_param("estate_kit.pool_min_listing_score", "3"))
        t_include = float(get_param("estate_kit.pool_inclusion_threshold", "7.0"))
        t_exclude = float(get_param("estate_kit.pool_exclusion_threshold", "4.0"))
        pool_max = int(get_param("estate_kit.pool_max_size", "100"))

        self._marketing_pool.calculate_all()

        pool_properties = self._env["estate.property"].search([("tag_ids", "in", pool_tag.id)])
        for prop in pool_properties:
            if prop.state not in POOL_ELIGIBLE_STATES:
                self._pool_remove(prop, pool_tag, "Объект в статусе «%s»" % prop.state)
                continue

            latest = prop.scoring_ids[:1]
            if latest and self._marketing_pool.scores_below_threshold(latest, min_price, min_quality, min_listing):
                self._pool_remove(
                    prop, pool_tag,
                    "AI-скоринг ниже порога: price=%d quality=%d listing=%d"
                    % (latest.price_score, latest.quality_score, latest.listing_score),
                )
                continue

            mps = prop.marketing_pool_score
            if mps < t_exclude:
                if self._is_pool_protected(prop):
                    prop.activity_schedule(
                        act_type_xmlid="mail.mail_activity_data_todo",
                        summary="MPS ниже порога — проверьте",
                        note="Marketing Pool Score: %.1f (порог: %.1f). "
                             "Объект защищён от исключения." % (mps, t_exclude),
                    )
                else:
                    self._pool_remove(
                        prop, pool_tag,
                        "MPS %.1f ниже порога %.1f" % (mps, t_exclude),
                    )

        pool_count = self._env["estate.property"].search_count([("tag_ids", "in", pool_tag.id)])
        free_slots = pool_max - pool_count
        if free_slots <= 0:
            return

        candidates = self._env["estate.property"].search([
            ("tag_ids", "not in", pool_tag.ids),
            ("state", "in", list(POOL_ELIGIBLE_STATES)),
            ("marketing_pool_score", ">=", t_include),
        ], order="marketing_pool_score desc", limit=free_slots)

        for prop in candidates:
            latest = prop.scoring_ids[:1]
            if not latest:
                continue
            if self._marketing_pool.scores_below_threshold(latest, min_price, min_quality, min_listing):
                continue

            prop.tag_ids += pool_tag
            prop.message_post(
                body="Включён в маркетинговый пул (MPS: %.1f)" % prop.marketing_pool_score,
                message_type="comment",
                subtype_xmlid="mail.mt_note",
            )
            _logger.info("Property %s added to pool (MPS: %.1f)", prop.id, prop.marketing_pool_score)

    def create_callback_activities(self) -> None:
        marketing_tag = self._env.ref(
            "estate_kit.property_tag_marketing_pool", raise_if_not_found=False
        )
        if not marketing_tag:
            _logger.warning("Marketing Pool tag not found, skipping callback cron")
            return

        properties = self._env["estate.property"].search([("tag_ids", "in", marketing_tag.ids)])
        if not properties:
            return

        activity_type = self._env.ref("mail.mail_activity_data_todo")
        model_id = self._env["ir.model"]._get_id("estate.property")
        note = (
            "<ul>"
            "<li>Объект ещё в продаже?</li>"
            "<li>Изменилась ли цена?</li>"
            "<li>Есть ли обновления по объекту?</li>"
            "</ul>"
        )

        for prop in properties:
            responsible_user = prop.user_id or prop.listing_agent_id
            if not responsible_user:
                continue
            self._env["mail.activity"].create({
                "activity_type_id": activity_type.id,
                "summary": "Обзвон: проверка актуальности",
                "note": note,
                "res_model_id": model_id,
                "res_id": prop.id,
                "user_id": responsible_user.id,
            })

        _logger.info(
            "Callback activities created for %d properties in marketing pool",
            len(properties),
        )

    def _is_pool_protected(self, prop) -> bool:
        get_param = self._env["ir.config_parameter"].sudo().get_param
        protect_priority = int(get_param("estate_kit.tier_lead_protection_priority", "5"))

        lead_tiers = prop.tier_ids.filtered(lambda t: t.role == "team_lead")
        if lead_tiers and min(t.priority for t in lead_tiers) <= protect_priority:
            return True

        active_with_leads = prop.placement_ids.filtered(
            lambda p: p.state == "active" and p.leads_count > 0
        )
        if active_with_leads:
            return True

        return False

    def _pool_remove(self, prop, pool_tag, reason: str) -> None:
        prop.tag_ids -= pool_tag
        active_placements = prop.placement_ids.filtered(
            lambda p: p.state in ("draft", "active", "paused")
        )
        if active_placements:
            active_placements.write({"state": "removed"})
        prop.message_post(
            body="Выведен из маркетингового пула: %s" % reason,
            message_type="comment",
            subtype_xmlid="mail.mt_note",
        )
        _logger.info("Property %s removed from pool: %s", prop.id, reason)
