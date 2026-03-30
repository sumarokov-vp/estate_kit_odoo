# CLAUDE.md

## Описание проекта

Estate Kit — модуль для Odoo 19, управление недвижимостью.

**Продакшн:** https://royalestate.smartist.dev/

## Структура проекта

```
addons/estate_kit/    # Odoo модуль
build/                # Dockerfile и compose для сборки образа
podman/               # Compose для локальной разработки (podman)
docker/               # Compose для сервера (docker)
```

## Odoo модуль

- Версия: 19.0
- Путь: `addons/estate_kit/`
- Зависимости: `base`, `mail`
- Модели: `estate.property` — объект недвижимости
- Обновление: Apps → Estate Kit → Upgrade или `odoo -u estate_kit -d <database>`

## Локальная разработка

```bash
cd podman && cp .env.example .env && podman-compose up -d
```

Сборка образа: `cd build && podman-compose build`

## База данных

PostgreSQL (внешний). Настройки в `.env`: `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD`.

## Архитектура: DDD-структура моделей

Каждая Odoo-модель (или группа связанных моделей) живёт в `addons/estate_kit/src/<domain>/` — это bounded context. Модель остаётся тонкой (поля + однострочные делегаты), вся логика выносится в сервисы.

### Структура домена

```
src/<domain>/
├── __init__.py              # from . import models
├── models/
│   ├── __init__.py          # from . import <model_file>
│   └── <model>.py           # Odoo-модель: поля + тонкие методы-делегаты
└── services/
    ├── __init__.py
    └── <service_name>/      # Каждый сервис — отдельный пакет
        ├── __init__.py      # Реэкспорт: Factory + публичные типы
        ├── factory.py       # Factory — composition root
        ├── service.py       # Фасад — тонкий класс, делегирует зависимостям
        ├── protocols/       # typing.Protocol для зависимостей
        │   ├── __init__.py
        │   └── i_<name>.py  # Один протокол = один файл, один метод
        ├── <impl>.py        # Реализации: один класс = один публичный метод = один файл
        ├── config.py        # Конфигурация (dataclass, ir.config_parameter)
        └── <data>.py        # Данные (константы, маппинги)
```

### Принцип тонкой модели

Odoo-модель содержит только:
- Определения полей (`fields.*`)
- `@api.depends` / `@api.onchange` — вызывают сервис в одну строку
- `create()` / `write()` — вызывают сервис, затем `super()`
- `action_*` кнопки — однострочные делегаты к сервису
- `_sql_constraints`

Вся бизнес-логика, валидация, внешние вызовы — в сервисах.

```python
# Модель (тонкая):
class CrmLead(models.Model):
    _inherit = "crm.lead"

    def action_set_won(self):
        result = super().action_set_won()
        DealCreatorFactory.create(self.env).create_if_not_exists(self)
        return result
```

### Правила сервисов

**Главное правило: никаких приватных методов (`_method`) в сервисах.** Если нужна вспомогательная логика — это отдельный класс в отдельном файле, внедряемый через DI.

**Фасад (service.py):**
- Единый класс, все публичные методы сервиса в одном месте
- Тонкий: не содержит бизнес-логики, делегирует зависимостям
- Зависимости через конструктор (DI), типизированные протоколами
- Никаких приватных методов — только `__init__` и публичные методы-делегаты

**Реализации (один класс = один файл = один публичный метод):**
- Класс выполняет одну операцию через единственный публичный метод
- Если реализации нужна вспомогательная логика — это ещё один класс, внедряемый через DI
- Зависимости через конструктор, типизированные протоколами
- Имя файла = имя класса в snake_case (например, `pool_remover.py` → `PoolRemover`)

**Протоколы (protocols/):**
- `typing.Protocol` — structural subtyping, реализации НЕ наследуют протоколы
- Имена с префиксом `I`: `IAiClient`, `IThresholdChecker`
- Один протокол = один файл, один метод
- Каждая зависимость фасада и реализаций типизирована протоколом

**Фабрика (factory.py):**
- Класс `Factory` со статическими методами — composition root
- Собирает граф зависимостей, создаёт конкретные реализации, возвращает фасад
- Единственное место, знающее о конкретных классах

**Использование чужих сервисов:**
- Сервис может зависеть от классов из другого сервиса (из своего или чужого домена)
- Зависимость оформляется через протокол в `protocols/` текущего сервиса
- Фабрика импортирует конкретную реализацию и передаёт в конструктор
- Прямой импорт чужих реализаций — только в фабрике, никогда в фасаде или реализациях

**Совместимость с Odoo:**
- Модели вызывают `Factory.create(env, ...)` и работают с фасадом
- `env` (Odoo Environment) передаётся в фабрику, не в фасад
- Сервисы не импортируют из models/controllers

### Цепочка импортов

```
addons/estate_kit/__init__.py      → from . import src
src/__init__.py                     → from . import lead, property
src/<domain>/__init__.py            → from . import models
src/<domain>/models/__init__.py     → from . import <model_file>
```

### Домен `erp_core` — интеграция с библиотекой erp-core

Домен `src/erp_core/` управляет отдельной PostgreSQL-базой ERP Core (сделки, счета, платежи). Схема и данные управляются через yoyo-миграции.

**Структура:**
```
src/erp_core/
├── config.py                  # get_database_url() из ENV
├── migrations/                # Клиентские SQL-миграции
│   └── c0001.seed-reference-data.sql
└── services/
    └── initializer/           # Запуск миграций при установке модуля
```

**Добавление клиентской миграции или обновление erp-core:**

В обоих случаях нужно применить миграции ERP Core через Odoo post-migrate. Порядок действий:

1. Создать файл `src/erp_core/migrations/c<NNNN>.<описание>.sql` (если клиентская миграция)
2. В первой строке указать зависимость: `-- depends: <предыдущая миграция>`
3. Поднять версию модуля в `__manifest__.py`
4. Создать Odoo-миграцию `migrations/<version>/post-migrate.py` с вызовом `Initializer`:

```python
import logging
_logger = logging.getLogger(__name__)

def migrate(cr, version):
    if not version:
        return
    try:
        from odoo.addons.estate_kit.src.erp_core.services.initializer.factory import Factory
        Factory.create().initialize()
    except Exception as e:
        _logger.warning("ERP Core migrations skipped: %s", e)
```

Это применит все непримененные миграции — как клиентские, так и библиотечные (при обновлении версии erp-core).

**Когда нужна Odoo post-migrate с Initializer:**
- Добавлена новая клиентская миграция (`c0002`, `c0003`...)
- Обновлена версия библиотеки erp-core (могут быть новые библиотечные миграции)

Пример клиентской миграции:
```sql
-- depends: c0001.seed-reference-data
ALTER TABLE party ADD COLUMN x_telegram_id BIGINT;
```

Конвенция именования: клиентские миграции с префиксом `c` (`c0001`, `c0002`...), библиотечные — числовые (`0001`, `0002`...).

### Устаревшие сервисы (legacy)

`addons/estate_kit/services/` — старые сервисы, не привязанные к домену. Новые сервисы создавать ТОЛЬКО в `src/<domain>/services/`. При рефакторинге — переносить из `services/` в соответствующий домен.

## Скиллы

| Скилл | Описание |
|-------|----------|
| `/deploy` | Деплой в production (делегирует devops агенту) |
| `/server-ops` | Серверные операции: логи, рестарт, SQL, обновление модуля, troubleshooting |
| `/web_testing` | Тестирование через браузер (Playwright): скриншоты, клики, проверка UI |
