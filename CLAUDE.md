# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Описание проекта

Royal Estate — модуль для Odoo 19, управление недвижимостью.

## Структура проекта

```
addons/royal_estate/    # Odoo модуль
build/                  # Dockerfile и compose для сборки образа
podman/                 # Compose для локальной разработки (podman)
docker/                 # Compose для сервера (docker)
```

## Команды

### Сборка образа
```bash
cd build && podman-compose build
```

### Локальная разработка (podman)
```bash
cd podman && cp .env.example .env && podman-compose up -d
```

### Серверный деплой (docker)
```bash
cd docker && cp .env.example .env && docker compose up -d
```

## База данных

PostgreSQL запускается отдельно (внешний). Настройки подключения в `.env`:
- `DB_HOST` — хост PostgreSQL
- `DB_PORT` — порт (по умолчанию 5432)
- `DB_USER` — пользователь
- `DB_PASSWORD` — пароль

## Odoo модуль

- Версия: 19.0
- Путь: `addons/royal_estate/`
- Зависимости: `base`, `mail`

### Модели
- `estate.property` — объект недвижимости

### Обновление модуля
В интерфейсе Odoo: Apps → Royal Estate → Upgrade
Или через CLI: `odoo -u royal_estate -d <database>`
