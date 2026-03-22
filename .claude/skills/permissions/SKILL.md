---
name: permissions
description: Справочник по системе прав Estate Kit. Привилегии, группы, иерархия, ACL, record rules. Используй когда нужно понять или изменить права доступа пользователей.
---

# Система прав Estate Kit

## Архитектура прав

В Estate Kit используется двухуровневая система прав Odoo:

1. **ACL (ir.model.access.csv)** — модельный уровень: какие операции (read/write/create/unlink) разрешены группе на модели
2. **Record Rules (estate_security.xml)** — уровень записей: какие конкретно записи видит/может менять пользователь

## Привилегии (dropdowns)

В настройках пользователя (Settings → Users → выбрать пользователя) в секции "Estate Kit" есть **два dropdown-селектора**:

### Привилегия "Листинг"

Контролирует доступ к объектам недвижимости (`estate.property`).

| # | Уровень | XML ID группы | Права на property | Видимость записей |
|---|---------|---------------|-------------------|-------------------|
| 1 | ISA | `group_estate_isa` | Чтение | Опубликованные + свои |
| 2 | Buyer's Agent | `group_estate_buyer_agent` | Чтение | Опубликованные + свои |
| 3 | Transaction Coordinator | `group_estate_transaction_coordinator` | Чтение | Все записи |
| 4 | Listing Agent | `group_estate_listing_agent` | Чтение + запись + создание | Свои + shared |
| 5 | Listing Coordinator | `group_estate_listing_coordinator` | Чтение + запись + создание | Все записи |
| 6 | Team Lead | `group_estate_team_lead` | Полный CRUD | Все записи |

**Иерархия линейная:** каждый уровень включает все права предыдущего через `implied_ids`. Listing Agent автоматически получает права Transaction Coordinator, Buyer's Agent и ISA.

### Привилегия "Маркетинг"

Контролирует доступ к рекламным размещениям (`estate.property.placement`).

| # | Уровень | XML ID группы | Права на placement | Права на property |
|---|---------|---------------|--------------------|-------------------|
| 1 | Marketing Viewer | `group_estate_marketing_viewer` | Чтение | Чтение (все) |
| 2 | Marketing Manager | `group_estate_marketing` | Полный CRUD | Чтение (все) |
| 3 | Team Lead | `group_estate_marketing_lead` | Полный CRUD | Чтение (все) |

**Привилегии независимы.** Пользователь может иметь уровень в каждой привилегии одновременно (например, Listing Agent + Marketing Manager).

## Где настраивать

### Назначение ролей пользователю
**Settings → Users & Companies → Users → (выбрать пользователя)**

В форме пользователя, секция "Estate Kit":
- Dropdown "Листинг" — выбрать уровень доступа к объектам
- Dropdown "Маркетинг" — выбрать уровень доступа к размещениям

### Изменение прав группы (ACL)
**Файл:** `addons/estate_kit/security/ir.model.access.csv`

Каждая строка: `id, name, model_id, group_id, read, write, create, unlink`

### Изменение видимости записей (Record Rules)
**Файл:** `addons/estate_kit/security/estate_security.xml`

Секция `ir.rule` — домены фильтрации для каждой группы.

### Изменение порядка уровней в dropdown
**Файл:** `addons/estate_kit/security/estate_security.xml`

Поле `<field name="sequence">` в записи группы (`res.groups`). Меньше sequence = ниже уровень в иерархии.

### Добавление нового уровня
1. Создать группу (`res.groups`) с `privilege_id` и правильным `sequence`
2. Установить `implied_ids` — ссылку на предыдущий уровень
3. Обновить `implied_ids` следующего уровня — ссылку на новую группу
4. Добавить ACL строки в `ir.model.access.csv`
5. При необходимости добавить record rules

## Текущее покрытие ACL

Группы имеют ACL на следующие модели:
- `estate.property` — объекты недвижимости
- `estate.property.image` — фото объектов
- `estate.property.placement` — рекламные размещения
- `estate.property.scoring` — скоринг объектов
- `estate.property.tier` — тир-листы
- `estate.property.tag` — теги
- `estate.city`, `estate.district`, `estate.street` — география
- `estate.source` — источники
- `estate.climate.equipment`, `estate.appliance` — оборудование
- `krisha.parser.*` — парсер Крыша.кз
- `estatekit.webhook.event` — webhook-события

$ARGUMENTS
