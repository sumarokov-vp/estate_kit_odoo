---
name: deploy
description: Деплой Odoo в выбранное окружение (Dev или Prod).
allowed-tools: Bash(.claude/skills/deploy/scripts/*)
---

Деплой Odoo. $ARGUMENTS

## Инструкции

При вызове спроси пользователя какое окружение использовать: **Dev** или **Prod**.

### Dev

Рестартует контейнер Odoo в общем dev docker-compose (`estate_kit/dev/docker-compose.yml`). Аддоны подключены через volume (`../odoo/addons`), билд не нужен.

```bash
uv run python .claude/skills/deploy/scripts/deploy_dev.py
```

### Prod

**Делегируй выполнение агенту devops.**

> `uv run python .claude/skills/deploy/scripts/deploy-prod.py`
>
> Конфиг деплоя в `.claude/devops.yaml` (секция `deploy`), сервер резолвится из `servers` по имени.
>
> Для проверки без реального деплоя: `uv run python .claude/skills/deploy/scripts/deploy-prod.py --dry-run`

Не выполняй prod деплой-скрипты самостоятельно — всегда делегируй devops агенту.
