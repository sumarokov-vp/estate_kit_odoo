---
name: deploy
description: Деплой Odoo в production. Требует агента devops для выполнения.
allowed-tools: Bash(.claude/skills/deploy/scripts/*)
---

Деплой Odoo в production. $ARGUMENTS

## Инструкции

**Делегируй выполнение агенту devops** через Task tool (subagent_type: devops).

Передай агенту следующую задачу:

> Выполни production деплой Odoo. Запусти скрипт:
> `uv run python .claude/skills/deploy/scripts/deploy-prod.py`
>
> Конфиг деплоя в `.claude/devops.yaml` (секция `deploy`), сервер резолвится из `servers` по имени.
>
> Для проверки без реального деплоя: `uv run python .claude/skills/deploy/scripts/deploy-prod.py --dry-run`

Не выполняй деплой-скрипты самостоятельно — всегда делегируй devops агенту.
