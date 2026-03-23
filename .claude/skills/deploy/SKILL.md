---
name: deploy
description: Деплой Odoo в выбранное окружение (Dev или Prod).
allowed-tools: Bash(.claude/skills/deploy/scripts/*)
---

Деплой Odoo. $ARGUMENTS

## Инструкции

При вызове спроси пользователя какое окружение использовать: **Dev**, **Prod** или **Docs**.

### Dev

Рестартует контейнер Odoo в общем dev docker-compose (`estate_kit/dev/docker-compose.yml`). Аддоны подключены через volume (`../odoo/addons`), билд не нужен.

```bash
uv run python .claude/skills/deploy/scripts/deploy_dev.py
```

### Prod

**Делегируй выполнение агенту devops.**

> `uv run python .claude/skills/deploy/scripts/deploy-prod.py`
>
> Структура деплоя в `.claude/devops.yaml`, credentials в `pass agent_fleet/projects/estate-kit/odoo`
>
> Для проверки без реального деплоя: `uv run python .claude/skills/deploy/scripts/deploy-prod.py --dry-run`

Не выполняй prod деплой-скрипты самостоятельно — всегда делегируй devops агенту.

### Docs

Публикует пользовательскую и/или техническую документацию (MkDocs) на продакшн.

**Делегируй выполнение агенту devops.**

> `uv run python .claude/skills/deploy/scripts/deploy-docs.py`
>
> Опции:
> - `--site user` — только пользовательская документация
> - `--site tech` — только техническая документация
> - без `--site` — обе
> - `--dry-run` — проверка без реального деплоя
>
> Скрипт собирает MkDocs-сайты, rsync-ает на сервер, обновляет Caddyfile.
>
> URLs:
> - https://royalestate.smartist.dev/docs/user/
> - https://royalestate.smartist.dev/docs/tech/
