---
name: docs-access
description: Управление доступом к технической документации CRM (crm-docs.estate-kit.com). Добавление/удаление пользователей, просмотр списка доступов. Используй когда пользователь просит дать или забрать доступ к CRM-документации.
allowed-tools: Bash(.claude/skills/docs-access/scripts/*)
---

## Документация CRM

- Домен: `crm-docs.estate-kit.com`
- Авторизация: Cloudflare Access (OTP на email)
- Cloudflare Access App ID: `73dc1b87-bb51-4336-b330-21fc83213d1c`

## Команды

```bash
users.sh list                              # Кто имеет доступ
users.sh add user@example.com              # Дать доступ
users.sh add user1@ex.com user2@ex.com     # Дать доступ нескольким
users.sh remove user@example.com           # Забрать доступ
users.sh add-domain example.com            # Доступ всем с домена
```

## Правила

- Всегда `list` перед изменениями — показать текущее состояние
- При удалении подтвердить email с пользователем
- Сообщить пользователю, что вход по одноразовому коду на email (OTP)
