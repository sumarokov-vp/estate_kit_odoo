---
name: deploy
description: Деплой Estate Kit на продакшн сервер.
allowed-tools: Bash(.claude/skills/deploy/scripts/*)
---

Деплой Estate Kit на продакшн сервер. $ARGUMENTS

## Инструкции

Перед запуском убедись, что в `.env` заполнены переменные:
- `DEPLOY_SSH_KEY` — путь к SSH-ключу
- `DEPLOY_USER` — пользователь на сервере
- `DEPLOY_HOST` — адрес сервера
- `DEPLOY_IMAGE` — имя Docker-образа
- `DEPLOY_SERVER_PATH` — директория на сервере
- `DEPLOY_CONTAINER` — имя контейнера Odoo
- `DEPLOY_DB_NAME` — имя базы данных

```bash
.claude/skills/deploy/scripts/deploy.sh
```

При ошибке покажи лог и помоги разобраться.

Сайт: https://royalestate.smartist.dev/
