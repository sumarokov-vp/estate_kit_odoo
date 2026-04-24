# Система оценки стоимости (Market Pricing)

Руководство по подготовке и эксплуатации системы формульной оценки цен
объектов недвижимости на основе снапшотов рынка и hedonic-коэффициентов.

Добавлена в версии модуля **19.0.1.16.0** (миграция post-migrate создаёт
таблицы, коэффициенты). В **19.0.1.18.0** сборщик Krisha был вынесен
из Odoo-модуля в отдельный sidecar-проект — см. раздел
[«Инфраструктура сбора»](#инфраструктура-сбора) ниже. В **19.0.1.19.0**
снапшот хранит сырые сэмплы (`samples_per_sqm double precision[]`),
а резолвер агрегирует несколько снапшотов одного среза за окно — это
сглаживает скачки между соседними сборами и расширяет выборку.

## Как это работает (кратко)

1. **Внешний sidecar-процесс** `krisha_snapshots` (docker-compose на
   dev-сервере, KZ-IP) запускается каждые 2 часа. Берёт первые
   `MAX_TARGETS_PER_RUN` (по умолчанию 5) самых старых targets из
   `estate.market.snapshot.config` и обрабатывает их. Если самый старый
   target моложе `FRESHNESS_THRESHOLD_DAYS` (по умолчанию 14) — запуск
   пропускается. Так срезы постепенно обновляются и не нагружают Krisha.
2. Для каждого среза парсер считает `price / area` по ~100-300
   объявлениям, фильтрует чужие комнатности, обрезает 5% выбросов,
   пишет медиану, P25, P75 **и сырой массив `samples_per_sqm`** в
   `estate.market.snapshot` (минимум 20 объявлений, иначе пропуск).
3. **Для городских apartment-срезов** (`district_id IS NULL`) sidecar
   дополнительно разбивает выдачу по районам: из подзаголовка карточки
   на Krisha (`Бостандыкский р-н, мкр …`) извлекается имя района, по
   `estate_district.krisha_name` находится `district_id`, и для каждого
   района пишется отдельный snapshot с теми же `city/property_type/rooms`.
   Это даёт районные медианы без дополнительных HTTP-запросов и без
   серверного фильтра Krisha по району (он не работает).
4. При AI-скоринге объекта:
   - `BenchmarkResolverService` собирает снапшоты по цепочке релаксации
     `exact → no_rooms → city_only` — берёт последние N снапшотов
     одного среза за `window_days`, объединяет их `samples_per_sqm` в
     одну выборку и пересчитывает медиану/P25/P75. Если у найденных
     снапшотов нет сырых сэмплов (старые до 19.0.1.19.0) — fallback на
     медиану одиночного `find_latest`.
   - `PriceScoreCalculator` умножает медиану на hedonic-множитель
     (этаж, паркинг, состояние, год постройки), сравнивает с
     `price / area_total` объекта и даёт `price_score` от 1 до 10.
   - Если snapshot не найден — fallback на LLM (с пометкой в rationale).

## Хранение сырых сэмплов и агрегация

Колонка `samples_per_sqm double precision[]` создаётся через `init()`
модели `estate.market.snapshot` (`ALTER TABLE ADD COLUMN IF NOT EXISTS`),
накатывается при `-u estate_kit`.

Параметры агрегации (`BenchmarkResolverConfig`):

| Параметр                       | Default | Смысл                                  |
|--------------------------------|---------|----------------------------------------|
| `window_days`                  | 30      | возрастной фильтр снапшотов            |
| `aggregation_snapshots_limit`  | 10      | сколько последних снапшотов одного среза смержить |
| `min_aggregated_sample_size`   | 30      | минимум объединённой выборки, иначе fallback |

Алгоритм объединения — простая конкатенация массивов с равными весами,
median/P25/P75 считаются на объединённой выборке. Взвешивание по
recency пока не используется — если потребуется, добавить декей
exp(-age/half_life) в `SampleAggregator.aggregate`.

## Инфраструктура сбора

### Почему отдельный проект (sidecar)

Prod-сервер Odoo находится в DigitalOcean Frankfurt (AS14061).
Krisha.kz agressively блокирует IP из datacenter-ASN: эмпирически —
после ~25-30 HTTP-запросов IP уходит в silent-drop на часы/сутки (не
403, не CAPTCHA — TCP просто не отвечает). Попытки обойти через
User-Agent, pacing, retries не спасают — корневая причина в geo/ASN.

Dev-сервер `sumarokov-home` находится в Казахстане (Kar-Tel,
residential FTTB). С KZ-residential IP anti-bot Krisha не срабатывает
даже при 90+ запросах подряд.

**Вывод:** сбор рыночных данных перенесён с prod на dev-сервер.
Парсер работает там, а снапшоты пишет в prod-БД через SSH-туннель.

### Архитектурная схема

```
┌──────────────────────────────────────┐  ┌──────────────────────────┐
│ dev-сервер sumarokov-home (KZ)       │  │ prod: royal_estate_odoo  │
│ внешний IP 37.99.66.15 (Kar-Tel)     │  │ (DO Frankfurt)           │
│                                      │  │                          │
│ ~/projects/estate_kit/krisha_snapshots│  │  odoo-odoo-1 (Odoo 19)   │
│                                      │  │         ↓                │
│  docker compose:                     │  │  estate_market_snapshot  │
│  ┌────────────────────────────────┐  │  │  estate_market_snapshot_ │
│  │ ssh-tunnel (alpine+openssh)    │──┼──┼─→  config                │
│  │  ssh -N -L 5432:10.114.0.2:5432│  │  │                          │
│  │      royal_estate_odoo         │  │  │  ┌───────────────────┐   │
│  └────────────────────────────────┘  │  │  │ PG 10.114.0.2:5432│   │
│  ┌────────────────────────────────┐  │  │  │ (DO Managed PG    │   │
│  │ collector (python 3.14)        │  │  │  │  в VPC, доступен  │   │
│  │  supercronic: 0 4 * * *        │  │  │  │  только изнутри)  │   │
│  │  → python -m krisha_snapshots  │  │  │  └───────────────────┘   │
│  │     HTTP GET krisha.kz (KZ IP) │  │  └──────────────────────────┘
│  │     psycopg → ssh-tunnel:5432  │──┘
│  └────────────────────────────────┘
└──────────────────────────────────────┘
```

### Состав проекта `krisha_snapshots`

- Путь: `/home/sumarokov/projects/estate_kit/krisha_snapshots/` (отдельный git-репо)
- Стек: Python 3.14, `uv`, `httpx`, `beautifulsoup4`, `psycopg`, `pydantic-settings`
- Контейнеры: `ssh-tunnel` (alpine + openssh-client), `collector` (python:3.14-slim + supercronic)
- Cron-расписание: `0 */2 * * *` (каждые 2 часа `Asia/Almaty`, задаётся в `docker/crontab`); collector сам решает, обрабатывать или пропускать запуск, по freshness
- Credentials: `pass agent_fleet/projects/estate-kit/odoo-db` — пароль Odoo-юзера PG

См. `README.md` проекта для детальной документации по разработке и локальному запуску.

### Операционные команды

```bash
cd ~/projects/estate_kit/krisha_snapshots

# Развернуть (первый раз или после обновления кода):
./scripts/deploy.sh

# Статус:
docker compose ps

# Логи (в реальном времени):
docker compose logs -f

# Запустить сбор вручную, не дожидаясь 04:00:
docker compose exec collector python -m krisha_snapshots

# Остановить:
docker compose down
```

### Почему UI-кнопка «Запустить сбор сейчас» удалена на prod

В версии модуля `19.0.1.18.0` кнопка и Odoo-cron убраны. Причина: с
prod-IP сбор заведомо не работает (IP забанен Krisha), а сама попытка
запуска создаёт «шумные» ошибки в логах и может триггерить новые баны.
Сбор теперь возможен **только** со sidecar на dev-сервере.

Если нужно запустить сбор вручную — зайди на dev-сервер и выполни
команду из блока выше.

### Troubleshooting

**Парсер не собирает данные / `connect_timeout` на krisha.kz.**
Проверить IP dev-сервера:

```bash
curl -s ipinfo.io/country  # ожидается: KZ
```

Если не KZ (провайдер сменил маршрутизацию, переехал сервер) — нужно
восстановить KZ residential IP через VPN или перенести sidecar.

**SSH-туннель падает / `Bad owner or permissions on /root/.ssh/config`.**
Entrypoint контейнера копирует ключи из `/mnt/ssh` (bind-mount на
`~/.ssh` хоста) в `/root/.ssh` с правильными правами (`700`/`600`).
Если проблема сохраняется — проверить пермиссии на хосте:

```bash
ls -la ~/.ssh/
```

и убедиться что SSH-alias `royal_estate_odoo` разрешается
(`ssh royal_estate_odoo whoami` должно отдать `root`).

**Connection failed: no pg_hba.conf entry for host "10.114.0.3".**
PG-сервер на 10.114.0.2 принимает подключения с IP prod-хоста
(10.114.0.3) только для юзера `odoo`. Юзер `sumarokov` (admin) ходит
только с хоста PG-сервера. Использовать юзера `odoo` — его пароль
лежит в pass `agent_fleet/projects/estate-kit/odoo-db`.

**Parser вернул 0 объявлений.**
Вероятно изменилась вёрстка Krisha. Проверить ручным curl, что
страница `https://krisha.kz/prodazha/kvartiry/almaty/` возвращает 200
и содержит блоки `div[data-id]`. При изменениях — адаптировать
`src/krisha_snapshots/krisha/listing_parser.py`.

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

### 2. Поднять sidecar-сборщик на dev-сервере

На dev-сервере (`sumarokov-home`, KZ IP):

```bash
cd ~/projects/estate_kit/krisha_snapshots
./scripts/deploy.sh
```

Проверка: `docker compose ps` — оба контейнера `Up`, ssh-tunnel
`healthy`. Подробнее — см. раздел
[«Инфраструктура сбора»](#инфраструктура-сбора) выше.

**В Odoo-модуле cron НЕТ** — начиная с версии `19.0.1.18.0` запись
`ir_cron` «Daily market snapshot collection from Krisha» удалена
миграцией (сбор с prod-IP блокируется Krisha).

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
данных по району). У района должно быть заполнено **`estate.district.krisha_name`**
— точное имя как пишет Krisha (например, `Алмалинский р-н`, `Алматы р-н`).
Sidecar использует именно `krisha_name`, не `name`. Если у района,
указанного в конфиге, `krisha_name` пустой — sidecar пропускает этот
target с warning'ом `district_without_krisha_name` (без поля сбор уйдёт
по всему городу и не имеет смысла).

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

На dev-сервере (sidecar):

```bash
cd ~/projects/estate_kit/krisha_snapshots
docker compose exec collector python -m krisha_snapshots
```

Один срез занимает ~15-17 секунд (5 страниц × 3 сек pacing + парсинг).
На 10 срезов — ~3 минуты.

### 5. Проверить результаты

**В Odoo UI на prod: Главное меню → Рынок → Снапшоты рынка** —
должны появиться записи с `sample_size ≥ 20`, `median_price_per_sqm`,
`p25_price_per_sqm`, `p75_price_per_sqm`.

**В логах sidecar** (на dev-сервере):

```bash
docker compose logs collector --tail 50
```

Ожидаемый итоговый лог: `{"message": "collect_end", "written": N, "skipped": 0, "errors": 0}`.

Если есть `skipped` / `errors` — предыдущие строки содержат причину
(`not enough samples`, `fetch failed`).

**В БД напрямую** (через SSH-туннель или `psql` на prod):

```sql
SELECT ci.name, s.rooms, s.sample_size, s.median_price_per_sqm, s.collected_at
FROM estate_market_snapshot s
JOIN estate_city ci ON ci.id = s.city_id
ORDER BY ci.name, s.rooms, s.collected_at DESC;
```

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
  изменилась вёрстка. Проверить ручным curl со sidecar, что страница
  возвращает 200 и содержит блоки `div[data-id]`. При изменениях —
  править `krisha_snapshots/src/krisha_snapshots/krisha/listing_parser.py`.
- **Район из конфига не совпадает с наименованием на Krisha** — URL
  уходит с параметром `das[map.district]=<name>`, но Krisha возвращает
  пусто. Снять район из конфига или поправить имя в `estate.district`.
- **Krisha блокирует dev-IP** — проверить `curl -s ipinfo.io/country`
  на dev-сервере (должно быть `KZ`). См. раздел
  [«Инфраструктура сбора → Troubleshooting»](#troubleshooting) выше.

### Для AI-скоринга `price_score` считает LLM, а не формула

- Нет свежего snapshot по цепочке (exact → no_rooms → city_only) в
  окне `window_days`. Добавить срез на нужный город/тип и запустить
  сбор на dev.
- У объекта пустой `city_id`, `property_type`, `price` или `area_total`
  — формула требует все четыре поля, иначе fallback.
- Проверить лог сбора и в логе скоринга отметку `(формула)` vs `(LLM)`.
  В `estate.property.scoring.rationale` при fallback будет суффикс
  «Оценка без рыночных данных: нет снапшота рынка для района/типа».

### Снапшоты собираются, но медианы дрейфуют

- Слишком узкий срез (малое `max_pages` или мало объявлений на рынке).
  Увеличить `max_pages`, либо объединить с городским срезом.
- Krisha отдаёт неоднородные объявления (суточная аренда, коммерция).
  Проверить URL в sidecar `krisha_snapshots/src/krisha_snapshots/krisha/url_builder.py` —
  `_CATEGORY_SLUG` должен указывать именно на продажу (`prodazha/...`).

---

## Файлы и модули

### Odoo-модуль `estate_kit`

| Компонент | Путь |
|-----------|------|
| Модель snapshot | `src/market_snapshot/models/estate_market_snapshot.py` |
| Модель конфига сбора | `src/market_snapshot/models/estate_market_snapshot_config.py` |
| Резолвер бенчмарка (для AI) | `src/market_snapshot/services/benchmark_resolver/` |
| Калькулятор оценки | `src/property/services/marketing_pool/price_score_calculator/` |
| Интеграция с AI | `src/property/services/ai_scoring/service.py` |
| Hedonic-параметры | `data/ir_config_parameter.xml` |
| UI (просмотр снапшотов, CRUD конфигов) | `views/estate_market_snapshot_views.xml`, `views/estate_menus.xml` |
| Миграции | `migrations/19.0.1.16.0/post-migrate.py` (создание), `migrations/19.0.1.18.0/post-migrate.py` (удаление obsolete cron) |

### Sidecar-проект `krisha_snapshots`

Отдельный git-репо в `/home/sumarokov/projects/estate_kit/krisha_snapshots/`.

| Компонент | Путь |
|-----------|------|
| Entry point | `src/krisha_snapshots/__main__.py` |
| URL-билдер (города, категории, комнаты) | `src/krisha_snapshots/krisha/url_builder.py` |
| HTTP-клиент (httpx) | `src/krisha_snapshots/krisha/http_client.py` |
| HTML-парсер (BS4 + jsdata fallback) | `src/krisha_snapshots/krisha/listing_parser.py` |
| Статистика (median, p25/p75, trim) | `src/krisha_snapshots/stats/` |
| Чтение конфига / запись снапшотов (psycopg) | `src/krisha_snapshots/db/` |
| Оркестратор | `src/krisha_snapshots/collector.py` |
| Composition root | `src/krisha_snapshots/factory.py` |
| Docker | `docker/collector.Dockerfile`, `docker/tunnel.Dockerfile`, `docker/crontab` |
| Compose | `compose.yaml` |
| Deploy | `scripts/deploy.sh` (читает pass → .env → compose up) |
