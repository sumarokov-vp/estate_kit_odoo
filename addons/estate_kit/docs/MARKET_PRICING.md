# Система оценки стоимости (Market Pricing)

Руководство по подготовке и эксплуатации системы формульной оценки цен
объектов недвижимости на основе снапшотов рынка и hedonic-коэффициентов.

Добавлена в версии модуля **19.0.1.16.0** (миграция post-migrate создаёт
таблицы, коэффициенты, cron).

## Как это работает (кратко)

1. **Cron** раз в сутки (`Daily market snapshot collection from Krisha`)
   обходит Krisha.kz по списку срезов (`estate.market.snapshot.config`):
   город + район (опц.) + тип объекта + комнаты.
2. Для каждого среза парсер считает `price / area` по ~100 объявлениям,
   обрезает 5% выбросов, пишет медиану, P25, P75 в
   `estate.market.snapshot` (минимум 20 объявлений на срез, иначе пропуск).
3. При AI-скоринге объекта:
   - `BenchmarkResolverService` ищет свежий snapshot по цепочке релаксации
     `exact → no_rooms → city_only`,
   - `PriceScoreCalculator` умножает медиану на hedonic-множитель
     (этаж, паркинг, состояние, год постройки), сравнивает с
     `price / area_total` объекта и даёт `price_score` от 1 до 10.
   - Если snapshot не найден — fallback на LLM (с пометкой в rationale).

Подробности реализации — см. коммиты `4ac310f`, `1a87d16`, `676cd8e`.

---

## Подготовка окружения: чек-лист

Порядок шагов — одинаковый для dev и prod. Отметьте [x] по мере выполнения.

### 1. Применить миграцию модуля

Миграция `19.0.1.16.0` создаёт модели `estate.market.snapshot`,
`estate.market.snapshot.config`, параметры `ir.config_parameter`
(hedonic-коэффициенты), и регистрирует cron.

- **Dev:** `uv run python .claude/skills/deploy/scripts/deploy_dev.py` —
  скрипт делает `-u estate_kit` на контейнере.
- **Prod:** `/deploy prod` (делегируется агенту devops), либо вручную
  `odoo -u estate_kit -d <database> --stop-after-init`.

Проверка: в БД появились таблицы `estate_market_snapshot`,
`estate_market_snapshot_config`:
```sql
SELECT COUNT(*) FROM estate_market_snapshot_config;
SELECT COUNT(*) FROM estate_market_snapshot;
```

### 2. Проверить cron

Cron регистрируется автоматически из `data/market_snapshot_cron.xml`.
Настраивать вручную на prod **не нужно** — миграция подхватит.

```sql
SELECT cron_name, active, lastcall, nextcall
FROM ir_cron ic
JOIN ir_act_server ias ON ias.id = ic.ir_actions_server_id
WHERE ias.code LIKE '%_cron_collect%';
```

Должна быть запись `Daily market snapshot collection from Krisha`,
`active=t`, `interval_type=days`, `interval_number=1`.

Если на prod ранее был отключён планировщик Odoo — убедиться, что
`--max-cron-threads > 0` в конфиге (по умолчанию 2, норм).

### 3. Завести срезы для сбора

Это единственный шаг, который **обязательно выполняется на каждом
окружении вручную** — таблица `estate.market.snapshot.config` не
засевается data-файлом (набор срезов зависит от того, в каких городах
работает клиент).

**Через UI:** Главное меню → **Рынок → Конфигурация сбора**
(группы доступа: `group_estate_team_lead`, `group_estate_marketing_lead`).

Минимальный базовый набор для агентства, работающего в Казахстане:

| Город | Тип       | Комнаты | max_pages |
|-------|-----------|---------|-----------|
| Алматы | apartment | 1       | 5         |
| Алматы | apartment | 2       | 5         |
| Алматы | apartment | 3       | 5         |
| Алматы | apartment | 4       | 5         |
| Алматы | apartment | 5       | 5         |
| Астана | apartment | 1       | 5         |
| Астана | apartment | 2       | 5         |
| Астана | apartment | 3       | 5         |
| Астана | apartment | 4       | 5         |
| Астана | apartment | 5       | 5         |

`max_pages=5` даёт ~100 объявлений на срез — стабильная медиана.

Срезы должны покрывать весь диапазон `rooms`, который встречается в базе
объектов. Если у клиента есть квартиры на 6+ комнат или студии (0), добавить
соответствующие срезы. При отсутствии точного среза резолвер откатывается
на `no_rooms` (latest snapshot по городу + типу без фильтра по комнатам),
но это даёт заниженную/завышенную медиану — формула будет неточной.

Если нужны срезы по районам — добавить их дополнительно (НЕ вместо
общегородских, т.к. резолвер всё равно откатится на город при отсутствии
данных по району). Имя района в `estate.district` должно совпадать с тем,
как его пишет Krisha (иначе URL уйдёт без фильтра по району и соберётся
срез по всему городу).

**Через SQL (быстрее на dev или при массовой заливке):**

```sql
-- Алматы (city_id = 1), Астана (city_id = 3) — проверить на своей БД
INSERT INTO estate_market_snapshot_config
    (city_id, district_id, property_type, rooms, max_pages, active,
     create_date, write_date, create_uid, write_uid)
VALUES
    (1, NULL, 'apartment', 1, 5, true, NOW(), NOW(), 1, 1),
    (1, NULL, 'apartment', 2, 5, true, NOW(), NOW(), 1, 1),
    (1, NULL, 'apartment', 3, 5, true, NOW(), NOW(), 1, 1),
    (1, NULL, 'apartment', 4, 5, true, NOW(), NOW(), 1, 1),
    (1, NULL, 'apartment', 5, 5, true, NOW(), NOW(), 1, 1),
    (3, NULL, 'apartment', 1, 5, true, NOW(), NOW(), 1, 1),
    (3, NULL, 'apartment', 2, 5, true, NOW(), NOW(), 1, 1),
    (3, NULL, 'apartment', 3, 5, true, NOW(), NOW(), 1, 1),
    (3, NULL, 'apartment', 4, 5, true, NOW(), NOW(), 1, 1),
    (3, NULL, 'apartment', 5, 5, true, NOW(), NOW(), 1, 1);
```

### 4. Запустить первый сбор вручную

**Через UI:** **Рынок → Запустить сбор сейчас** (меню доступно
`team_lead` / `marketing_lead`).

**Через CLI:**

```bash
docker exec -i <odoo-container> odoo shell -d <database> --no-http <<'PY'
from odoo.addons.estate_kit.src.market_snapshot.services.snapshot_collector.factory import Factory
Factory.create(env).collect_all()
env.cr.commit()
PY
```

Первый запуск занимает ~2 секунды на срез (HTTP запрос к Krisha + парсинг).
На 8 срезов — ~20 секунд.

### 5. Проверить результаты

**Главное меню → Рынок → Снапшоты рынка** — должны появиться записи
с `sample_size ≥ 20`, `median_price_per_sqm`, `p25`, `p75`.

**Логи сбора:**
```sql
SELECT timestamp, level, summary, details
FROM estate_kit_log
WHERE category='market_snapshot'
ORDER BY id DESC LIMIT 20;
```

Ожидаемый итоговый лог: `Сбор снапшотов завершён: записано=N, пропущено=0, ошибок=0`.

Если есть `пропущено` — в `details` будет причина
(`Недостаточно данных: получено N объявлений`, `Не удалось построить URL`).

### 6. (Опционально) Откалибровать hedonic-коэффициенты

Параметры в **Settings → Technical → Parameters → System Parameters**,
ключи `estate_kit.hedonic.*`:

| Ключ                                            | Default | Смысл                              |
|-------------------------------------------------|---------|------------------------------------|
| `estate_kit.hedonic.first_floor_penalty`        | 0.95    | множитель для 1-го этажа           |
| `estate_kit.hedonic.last_floor_penalty`         | 0.97    | множитель для последнего этажа     |
| `estate_kit.hedonic.parking_bonus`              | 1.03    | надбавка за подземный паркинг/гараж|
| `estate_kit.hedonic.year_built_penalty_per_decade` | 0.02 | штраф за каждые 10 лет возраста    |
| `estate_kit.hedonic.year_built_reference`       | 2015    | год, относительно которого штраф   |
| `estate_kit.hedonic.condition_no_repair_adj`    | 0.90    | состояние: без ремонта             |
| `estate_kit.hedonic.condition_cosmetic_adj`     | 0.97    | состояние: косметика               |
| `estate_kit.hedonic.condition_euro_adj`         | 1.05    | состояние: евро                    |
| `estate_kit.hedonic.condition_designer_adj`     | 1.10    | состояние: дизайнерский            |

Бакеты `deviation → score` зашиты в `price_score_calculator/config.py`
(`_DEFAULT_BUCKETS`). Шкала: −20% → 10, ±2% → 6, +20% → 3, +50% → 2,
выше → 1. Если нужно переопределить для сегмента (элитка, новостройки) —
потребуется правка кода, не параметров.

### 7. Прогнать AI-скоринг на нескольких объектах

Открыть карточку объекта с заполненными `price`, `area_total`, `city_id`,
`rooms`, `property_type` → кнопка **AI-скоринг**.

Проверить в логе:
```sql
SELECT timestamp, summary
FROM estate_kit_log
WHERE category='ai_scoring'
ORDER BY id DESC LIMIT 10;
```

Ожидаемый summary: `Ответ AI-скоринга: <name> → price=N (формула), ...`.
Если `(LLM)` — значит snapshot не нашёлся (нет среза для города/типа,
или snapshot протух по `window_days`). Проверить срезы и пересобрать.

---

## Типовые проблемы

### Все срезы пропущены, `sample_size=0`

- **Krisha отдаёт 200, но парсер не видит объявлений** — скорее всего
  изменилась вёрстка. См. `todos/148-krisha-jsdata-no-longer-contains-adverts.yaml`.
  Проверить ручным curl, что страница возвращает 200 и содержит
  `div[data-id]`; прогнать `HtmlFallbackParser.parse` на сохранённом
  HTML.
- **Район из конфига не совпадает с наименованием на Krisha** — URL
  уходит с параметром `das[map.district]=<name>`, но Krisha возвращает
  пусто. Снять район из конфига или поправить имя в `estate.district`.
- **Прокси/firewall блокирует исходящий трафик на krisha.kz** —
  `curl -v https://krisha.kz/prodazha/kvartiry/almaty/` из контейнера.

### Для AI-скоринга `price_score` считает LLM, а не формула

- Нет свежего snapshot по цепочке (exact → no_rooms → city_only) в
  окне `window_days`. Добавить срез на нужный город/тип и запустить
  сбор.
- У объекта пустой `city_id`, `property_type`, `price` или `area_total`
  — формула требует все четыре поля, иначе fallback.
- Проверить лог сбора и в логе скоринга отметку `(формула)` vs `(LLM)`.
  В `estate.property.scoring.rationale` при fallback будет суффикс
  «Оценка без рыночных данных: нет снапшота рынка для района/типа».

### Снапшоты собираются, но медианы дрейфуют

- Слишком узкий срез (малое `max_pages` или мало объявлений на рынке).
  Увеличить `max_pages`, либо объединить с городским срезом.
- Krisha отдаёт неоднородные объявления (суточная аренда, коммерция).
  Проверить URL в `krisha_search_url_builder.py` — `_CATEGORY_SLUG`
  должен указывать именно на продажу (`prodazha/...`).

---

## Файлы и модули

| Компонент | Путь |
|-----------|------|
| Модель snapshot | `src/market_snapshot/models/estate_market_snapshot.py` |
| Модель конфига сбора | `src/market_snapshot/models/estate_market_snapshot_config.py` |
| Сервис сбора | `src/market_snapshot/services/snapshot_collector/` |
| Сервис резолвера бенчмарка | `src/market_snapshot/services/benchmark_resolver/` |
| Калькулятор оценки | `src/property/services/marketing_pool/price_score_calculator/` |
| Интеграция с AI | `src/property/services/ai_scoring/service.py` |
| Cron | `data/market_snapshot_cron.xml` |
| Hedonic-параметры | `data/ir_config_parameter.xml` |
| UI | `views/estate_market_snapshot_views.xml`, `views/estate_menus.xml` |
| Миграция | `migrations/19.0.1.16.0/post-migrate.py` |
