# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Описание проекта

Estate Kit — модуль для Odoo 19, управление недвижимостью.

**Продакшн сайт:** https://royalestate.smartist.dev/

## Структура проекта

```
addons/estate_kit/    # Odoo модуль
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
- Путь: `addons/estate_kit/`
- Зависимости: `base`, `mail`

### Модели
- `estate.property` — объект недвижимости

### Обновление модуля
В интерфейсе Odoo: Apps → Estate Kit → Upgrade
Или через CLI: `odoo -u estate_kit -d <database>`

## Деплой на продакшн сервер

### SSH доступ

Параметры подключения в `.claude/devops.yaml` секция `servers.royal_estate_odoo`.

```bash
ssh -i ~/.ssh/id_ed25519 -o IdentitiesOnly=yes sumarokov@46.101.177.22
```

### Сборка и деплой образа

**ВАЖНО:** Запускать из корня проекта, не из папки build/

```bash
# Из корня проекта /Users/vladimirsumarokov/dev/vetrov/odoo
cd /Users/vladimirsumarokov/dev/vetrov/odoo
fish build/build.fish
```

Скрипт build.fish выполняет:
1. Сборка AMD64 образа с `--no-cache`
2. Push в registry docker.io/sumarokovvp/simplelogic:estate_kit_amd64
3. SSH на сервер → pull → down → up

### База данных на сервере

**КРИТИЧНО: База данных называется `royal_estate`, НЕ `vetrov`!**

Параметры подключения (получить из .env на сервере):
```bash
ssh royal_estate_odoo "cat /opt/odoo/.env | grep DB_"
```

Типичные значения:
- DB_HOST: 10.114.0.2 (внутренний IP DigitalOcean)
- DB_PORT: 5432
- DB_USER: odoo
- DB_PASSWORD: (см. .env на сервере)

### Обновление модуля на сервере через CLI

```bash
ssh royal_estate_odoo "docker exec odoo-odoo-1 odoo \
  --db_host=10.114.0.2 \
  --db_port=5432 \
  --db_user=odoo \
  --db_password=<PASSWORD_FROM_ENV> \
  -d royal_estate \
  -u estate_kit \
  --stop-after-init"
```

### Перезапуск Odoo на сервере

```bash
ssh royal_estate_odoo "cd /opt/odoo && docker compose down odoo && docker compose up -d odoo"
```

### Просмотр логов

```bash
ssh royal_estate_odoo "docker logs --tail 50 odoo-odoo-1"
```

### Проверка файлов в контейнере

```bash
# Проверить что файлы обновились
ssh royal_estate_odoo "docker exec odoo-odoo-1 cat /mnt/extra-addons/estate_kit/__manifest__.py"

# Проверить static файлы
ssh royal_estate_odoo "docker exec odoo-odoo-1 ls -la /mnt/extra-addons/estate_kit/static/src/"
```

### SQL запросы к базе (через контейнер)

```bash
ssh royal_estate_odoo "docker exec odoo-odoo-1 bash -c \"PGPASSWORD=<PASSWORD> psql -h 10.114.0.2 -U odoo -d royal_estate -c 'SELECT ...'\""
```

### Типичные проблемы

1. **View не обновляется** — удалить из ir_model_data и ir_ui_view, затем -u
2. **Assets не загружаются** — проверить __manifest__.py секцию assets
3. **ParseError в security.xml** — пометить записи как noupdate:
   ```sql
   UPDATE ir_model_data SET noupdate=true
   WHERE module='estate_kit' AND model IN ('ir.module.category', 'res.groups')
   ```

### Структура на сервере

- Путь к проекту: `/opt/odoo/`
- Docker compose: `/opt/odoo/compose.yaml`
- Переменные окружения: `/opt/odoo/.env`
- Контейнер Odoo: `odoo-odoo-1`
- Контейнер Traefik: `odoo-traefik-1`
