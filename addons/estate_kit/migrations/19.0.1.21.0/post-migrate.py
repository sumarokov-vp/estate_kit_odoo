"""Подчистка после введения district-split парсинга в sidecar.

Sidecar теперь сам разбивает городскую apartment-выдачу по районам
(через подзаголовок карточки), поэтому отдельные районные конфиги не
нужны — district-snapshot'ы пишутся автоматически из городского сбора.

Также убираем городские конфиги по коммерции/земле — текущий парсер
для них даёт мусорные данные (медианы в миллиардах ₸/м² для commercial,
0 sample для land), а специализированный парсер пока не готов.

Городским квартирам поднимаем max_pages 3→10, чтобы городская выдача
хватала на стабильную медиану по каждому из ~5-8 районов после split'а.

Дополнительно — удаляем уже записанные мусорные снапшоты commercial
(медиана > 1e9 ₸/м²), чтобы они не попадали в агрегацию резолвера.
"""

import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    if not version:
        return

    cr.execute(
        """
        DELETE FROM estate_market_snapshot_config
        WHERE district_id IS NOT NULL
           OR property_type IN ('commercial', 'land')
        """
    )
    deleted_configs = cr.rowcount
    _logger.info(
        "Удалено %s обсолетных конфигов (районные / commercial / land)",
        deleted_configs,
    )

    cr.execute(
        """
        UPDATE estate_market_snapshot_config
        SET max_pages = 10
        WHERE property_type = 'apartment'
          AND district_id IS NULL
          AND max_pages < 10
        """
    )
    _logger.info(
        "max_pages поднят до 10 для %s городских квартирных конфигов",
        cr.rowcount,
    )

    cr.execute(
        """
        DELETE FROM estate_market_snapshot
        WHERE property_type = 'commercial'
          AND median_price_per_sqm > 1e9
        """
    )
    _logger.info(
        "Удалено %s мусорных снапшотов commercial (медиана > 1e9)",
        cr.rowcount,
    )
