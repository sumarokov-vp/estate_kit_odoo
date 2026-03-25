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

**Фасад (service.py):**
- Единый класс, все публичные методы сервиса в одном месте
- Тонкий: не содержит бизнес-логики, делегирует зависимостям
- Зависимости через конструктор (DI), типизированные протоколами

**Протоколы (protocols/):**
- `typing.Protocol` — structural subtyping, реализации НЕ наследуют протоколы
- Имена с префиксом `I`: `IAiClient`, `IThresholdChecker`
- Один протокол = один файл, один метод

**Реализации:**
- Один класс = один публичный метод = один файл
- Зависимости через конструктор, типизированные протоколами

**Фабрика (factory.py):**
- Класс `Factory` со статическими методами — composition root
- Собирает граф зависимостей, создаёт конкретные реализации, возвращает фасад
- Единственное место, знающее о конкретных классах

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

### Устаревшие сервисы (legacy)

`addons/estate_kit/services/` — старые сервисы, не привязанные к домену. Новые сервисы создавать ТОЛЬКО в `src/<domain>/services/`. При рефакторинге — переносить из `services/` в соответствующий домен.

## Скиллы

| Скилл | Описание |
|-------|----------|
| `/deploy` | Деплой в production (делегирует devops агенту) |
| `/server-ops` | Серверные операции: логи, рестарт, SQL, обновление модуля, troubleshooting |
| `/web_testing` | Тестирование через браузер (Playwright): скриншоты, клики, проверка UI |
