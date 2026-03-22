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

## Архитектура сервисов

Каждый сервис в `addons/estate_kit/services/` оформляется как самостоятельный пакет (папка) с единым фасадом, протоколами и фабрикой. Это обеспечивает совместимость с Odoo (где нет DI-контейнера) и чистую архитектуру.

### Структура пакета сервиса

```
services/<service_name>/
├── __init__.py              # Реэкспорт: Factory + публичные типы
├── factory.py               # Factory — единственная точка сборки графа зависимостей
├── service.py               # Фасад — тонкий класс, делегирует всё внутренним зависимостям
├── protocols/               # Протоколы (typing.Protocol) для всех зависимостей
│   ├── __init__.py
│   └── <name>.py            # Один протокол = один файл, имя с префиксом I (IAiClient, IMpsCalculator)
├── <implementation>.py      # Реализации — один класс = один метод = один файл
├── config.py                # Конфигурация (dataclass, читает ir.config_parameter)
└── <data>.py                # Данные (промпты, маппинги, константы)
```

### Правила

**Фасад (service.py):**
- Единый класс, выставляемый наружу — все публичные методы сервиса в одном месте
- Тонкий: не содержит бизнес-логики, только делегирует вызовы внутренним зависимостям
- Принимает все зависимости через конструктор (DI), типизированные протоколами

**Протоколы (protocols/):**
- `typing.Protocol` — structural subtyping, реализации НЕ наследуют протоколы
- Имена с префиксом `I`: `IAiClient`, `IThresholdChecker`, `IMpsCalculator`
- Один протокол = один файл, один метод

**Реализации:**
- Один класс = один публичный метод = один файл
- Зависимости через конструктор, типизированные протоколами

**Фабрика (factory.py):**
- Класс `Factory` со статическими методами — composition root
- Собирает граф зависимостей, создаёт конкретные реализации, возвращает фасад
- Единственное место, знающее о конкретных классах — потребители работают только с фасадом

**Совместимость с Odoo:**
- Odoo-модели (controllers, models) вызывают `Factory.create(env, ...)` и работают с фасадом
- `env` (Odoo Environment) передаётся в фабрику, не в фасад напрямую
- Сервисы не импортируют из models/controllers (контракт lint-imports)

### Пример: marketing_pool

```python
# В Odoo-модели:
from ..services.marketing_pool import Factory as MarketingPoolFactory

service = MarketingPoolFactory.create(self.env, AnthropicClient(self.env))
service.calculate_all()
service.update_single(prop)
service.score_property(property_data)
```

## Скиллы

| Скилл | Описание |
|-------|----------|
| `/deploy` | Деплой в production (делегирует devops агенту) |
| `/server-ops` | Серверные операции: логи, рестарт, SQL, обновление модуля, troubleshooting |
| `/web_testing` | Тестирование через браузер (Playwright): скриншоты, клики, проверка UI |
