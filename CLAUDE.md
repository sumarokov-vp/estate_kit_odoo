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

## Скиллы

| Скилл | Описание |
|-------|----------|
| `/deploy` | Деплой в production (делегирует devops агенту) |
| `/server-ops` | Серверные операции: логи, рестарт, SQL, обновление модуля, troubleshooting |
| `/web_testing` | Тестирование через браузер (Playwright): скриншоты, клики, проверка UI |
