# Lead Services — Сервисы домена лидов

Описание сервисов, обрабатывающих жизненный цикл `crm.lead`.

---

## Обзор

При создании лида выполняется цепочка пост-обработки:

```
crm.lead.create()
    └── LeadCreatorService.after_create(records)
            ├── 1. ContactMatcherService.match_leads()   — поиск существующего контакта
            └── 2. ContactCreatorService.create_for_leads() — создание нового контакта
```

Цель: поле `partner_id` (Контакт) всегда заполнено после создания лида.

---

## ContactMatcherService

**Путь:** `src/lead/services/contact_matcher/`

Ищет существующий `res.partner` по совпадению телефона/мобильного.

### Алгоритм

1. Пропускает лиды, у которых `partner_id` уже установлен
2. Берёт `lead.phone` или `lead.mobile`
3. Нормализует номер (убирает всё кроме цифр, `8` → `7` для KZ/RU)
4. Ищет совпадение среди всех партнёров с телефоном
5. При совпадении — устанавливает `lead.partner_id`

### Структура

| Класс | Ответственность |
|-------|----------------|
| `ContactMatcherService` | Фасад: итерация по лидам, делегация поиска |
| `PartnerSearcher` | Поиск партнёра по нормализованному телефону |
| `PhoneNormalizer` | Нормализация телефонных номеров (KZ/RU) |

---

## ContactCreatorService (планируется)

**Путь:** `src/lead/services/contact_creator/`

Создаёт нового `res.partner` из данных лида, если матчер не нашёл существующего контакта.

### Алгоритм

1. Пропускает лиды, у которых `partner_id` уже установлен (заполнен матчером или вручную)
2. Повторно проверяет через матчер (`IContactMatcher`) — защита от дубликатов при batch-создании лидов
3. Если матчер нашёл — ставит `partner_id`, пропускает создание
4. Создаёт `res.partner` из данных лида:
   - `name` ← `lead.contact_name` или `lead.name`
   - `phone` ← `lead.phone`
   - `mobile` ← `lead.mobile`
   - `email` ← `lead.email_from`
   - `company_name` ← `lead.partner_name` (название компании, стандартное поле CRM)
5. Устанавливает `lead.partner_id` на созданного партнёра

### Структура

```
src/lead/services/contact_creator/
├── __init__.py              # Реэкспорт Factory
├── factory.py               # Composition root
├── service.py               # Фасад: итерация по лидам, делегация
├── partner_builder.py       # Сборка vals для res.partner из данных лида
├── orm_partner_creator.py   # Создание res.partner через ORM
└── protocols/
    ├── __init__.py
    ├── i_partner_builder.py # build(lead) -> dict
    └── i_partner_creator.py # create(vals) -> int (partner_id)
```

| Класс | Ответственность |
|-------|----------------|
| `ContactCreatorService` | Фасад: проверка `partner_id`, повторный матч, делегация создания |
| `PartnerBuilder` | Сборка словаря `vals` из полей лида для `res.partner` |
| `OrmPartnerCreator` | Вызов `env['res.partner'].create(vals)`, возврат `id` |

### Зависимости

- `IContactMatcher` (из `contact_matcher`) — повторная проверка перед созданием
- `IPartnerBuilder` — построение vals для партнёра
- `IPartnerCreator` — ORM-создание партнёра

### Интеграция в LeadCreatorService

```python
class LeadCreatorService:
    def __init__(self, contact_matcher, contact_creator):
        self._contact_matcher = contact_matcher
        self._contact_creator = contact_creator

    def after_create(self, records):
        self._contact_matcher.match_leads(records)
        self._contact_creator.create_for_leads(records)
```

Порядок важен: сначала матчер (дешёвая операция), потом создатель (только для оставшихся без контакта).
