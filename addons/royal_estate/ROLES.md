# Роли Royal Estate

## Справочник ролей

| XML ID | Название | Описание |
|--------|----------|----------|
| `group_estate_team_lead` | Team Lead | Полный доступ ко всему |
| `group_estate_listing_agent` | Listing Agent | Работа с объектами продавцов |
| `group_estate_buyer_agent` | Buyer's Agent | Работа с покупателями, просмотр объектов |
| `group_estate_isa` | ISA | Квалификация лидов, просмотр опубликованных объектов |
| `group_estate_listing_coordinator` | Listing Coordinator | Внесение объектов, загрузка фото, статусы |
| `group_estate_transaction_coordinator` | Transaction Coordinator | Документооборот, сопровождение сделок |

Все группы не-иерархические. Каждая наследует `base.group_user`. Один пользователь может иметь несколько ролей.

## Матрица доступов (ir.model.access)

| Модель | Team Lead | Listing Agent | Buyer's Agent | ISA | Listing Coord | Transaction Coord |
|--------|-----------|---------------|---------------|-----|---------------|-------------------|
| estate.property | CRUD | CRU | R | R | CRU | R |
| estate.property.image | CRUD | CRU | R | R | CRU | R |
| estate.city | CRUD | R | R | R | R | R |
| estate.district | CRUD | R | R | R | R | R |
| estate.street | CRUD | R | R | R | R | R |
| estate.source | CRUD | R | R | R | R | R |
| estate.climate.equipment | CRUD | R | R | R | R | R |
| estate.appliance | CRUD | R | R | R | R | R |
| krisha.parser.wizard | CRUD | CRUD | — | — | CRUD | — |
| krisha.parser.preview | CRUD | CRUD | — | — | CRUD | — |
| krisha.parser.result | CRUD | CRUD | — | — | CRUD | — |

## Record Rules (estate.property)

| Группа | Правило | Домен |
|--------|---------|-------|
| Team Lead | Все записи | `[(1,'=',1)]` |
| Listing Coordinator | Все записи | `[(1,'=',1)]` |
| Transaction Coordinator | Все записи (только чтение) | `[(1,'=',1)]` |
| Listing Agent | Свои + где он listing agent + открытые | `['⎮','⎮',('user_id','=',user.id),('listing_agent_id','=',user.id),('is_shared','=',True)]` |
| Buyer's Agent | Опубликованные + свои | `['⎮',('state','=','published'),('user_id','=',user.id)]` |
| ISA | Опубликованные + свои | `['⎮',('state','=','published'),('user_id','=',user.id)]` |

## Видимость меню

| Меню | Группы |
|------|--------|
| Недвижимость (root) | все 6 |
| Объекты | все 6 |
| Парсить Krisha.kz | Team Lead, Listing Agent, Listing Coordinator |
| Справочники | Team Lead |

## Маппинг должностей на роли (Этап 1: 3 человека)

| Сотрудник | Роли |
|-----------|------|
| Руководитель | Team Lead |
| Агент по листингу | Listing Agent, Listing Coordinator |
| ISA / Buyer's Agent | ISA, Buyer's Agent, Transaction Coordinator |
