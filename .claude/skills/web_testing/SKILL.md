---
name: web_testing
description: Тестирование Odoo через браузер (Playwright). Скриншоты, клики, проверка UI. Используй когда нужно проверить функциональность Odoo в браузере.
allowed-tools: Bash(.claude/skills/web_testing/scripts/*)
---

Тестирование Odoo CRM через headless-браузер. $ARGUMENTS

## Конфигурация

Креды для автологина в `.claude/devops.yaml`, секция `web_testing`:
- `url` — базовый URL Odoo
- `email` — логин
- `password` — пароль

## Скрипты

### Скриншот
```bash
uv run --with playwright --with pyyaml python .claude/skills/web_testing/scripts/screenshot.py <path_or_url> [filename.png]
```
`path_or_url` — полный URL или путь (например `/odoo/action-237`).

### Клик по элементу
```bash
uv run --with playwright --with pyyaml python .claude/skills/web_testing/scripts/click.py <path_or_url> <selector> [filename.png]
```

### Получить текст
```bash
uv run --with playwright --with pyyaml python .claude/skills/web_testing/scripts/text.py <path_or_url> <selector>
```

## Установка браузера (первый запуск)
```bash
uv run --with playwright python -m playwright install chromium
```
