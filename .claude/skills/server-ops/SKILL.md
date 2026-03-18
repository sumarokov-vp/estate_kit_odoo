---
name: server-ops
description: Серверные операции Odoo (логи, рестарт, SQL, проверка файлов, обновление модуля, troubleshooting). Используй когда нужно выполнить операцию на production сервере.
allowed-tools: Agent
---

Серверные операции Odoo на production. $ARGUMENTS

## Инструкции

**Делегируй выполнение агенту devops** через Agent tool (subagent_type: devops).

Сервер: `royal_estate_odoo` (из `.claude/devops.yaml`).

## Доступные операции

### Просмотр логов
```bash
ssh royal_estate_odoo "docker logs --tail 50 odoo-odoo-1"
```

### Перезапуск Odoo
```bash
ssh royal_estate_odoo "cd /opt/odoo && docker compose down odoo && docker compose up -d odoo"
```

### Обновление модуля на сервере
```bash
ssh royal_estate_odoo "docker exec odoo-odoo-1 odoo \
  --db_host=<DB_HOST> --db_port=5432 --db_user=odoo --db_password=<PASSWORD> \
  -d royal_estate -u estate_kit --stop-after-init"
```
Параметры БД получить: `ssh royal_estate_odoo "cat /opt/odoo/.env | grep DB_"`

### Проверка файлов в контейнере
```bash
ssh royal_estate_odoo "docker exec odoo-odoo-1 cat /mnt/extra-addons/estate_kit/__manifest__.py"
ssh royal_estate_odoo "docker exec odoo-odoo-1 ls -la /mnt/extra-addons/estate_kit/static/src/"
```

### SQL запросы
```bash
ssh royal_estate_odoo "docker exec odoo-odoo-1 bash -c \"PGPASSWORD=<PASSWORD> psql -h <DB_HOST> -U odoo -d royal_estate -c 'SELECT ...'\""
```

### Структура на сервере
- Путь: `/opt/odoo/`
- Compose: `/opt/odoo/compose.yaml`
- Env: `/opt/odoo/.env`
- Контейнеры: `odoo-odoo-1`, `odoo-traefik-1`

## База данных

**КРИТИЧНО: База данных называется `royal_estate`, НЕ `vetrov`!**

## Troubleshooting

1. **View не обновляется** — удалить из ir_model_data и ir_ui_view, затем -u
2. **Assets не загружаются** — проверить __manifest__.py секцию assets
3. **ParseError в security.xml** — пометить записи как noupdate:
   ```sql
   UPDATE ir_model_data SET noupdate=true
   WHERE module='estate_kit' AND model IN ('ir.module.category', 'res.groups')
   ```
