---
name: deploy
description: Деплой Estate Kit на продакшн сервер.
allowed-tools: Bash(.claude/skills/deploy/scripts/*)
---

Деплой Estate Kit на продакшн сервер. $ARGUMENTS

## Инструкции

```bash
uv run python .claude/skills/deploy/scripts/deploy-prod.py
```

Для проверки без реального деплоя:

```bash
uv run python .claude/skills/deploy/scripts/deploy-prod.py --dry-run
```

Конфиг читается из `.claude/devops.yaml` (секции `deploy`, `servers`).

При ошибке покажи лог и помоги разобраться.

Сайт: https://royalestate.smartist.dev/
