# Интеграции

## Архитектура системы

```
                              ┌─────────────────┐
                              │  ERP (Telegram) │
                              │  (зарплаты)     │
                              └────────▲────────┘
                                       │ API
                                       │ (сделки)
┌─────────────────┐           ┌────────┴────────┐
│  Estate Kit   │──────────▶│    Odoo CRM     │
│  (объекты)      │  привязка │    (сделки)     │
└─────────────────┘           └─────────────────┘
        │
 ┌──────┴──────┐
 ▼             ▼
┌───────────┐ ┌───────────┐
│ S3 Storage│ │   2GIS    │
│ (фото)    │ │ (карты)   │
└───────────┘ └───────────┘
```

**Ключевой момент:** ERP система работает с CRM (сделками), а не напрямую с базой объектов. Estate Kit — источник данных об объектах, CRM — источник данных о сделках для расчёта зарплат.

---

## 1. Odoo CRM — центр сделок

### Связь объекта со сделкой

```python
class EstateProperty(models.Model):
    _name = "estate.property"

    crm_lead_id = fields.Many2one(
        'crm.lead',
        string="Сделка",
        tracking=True
    )
```

### Автоматическое создание сделки

При переходе объекта в стадию "Задаток" создаётся сделка в CRM:

```python
@api.onchange('state')
def _onchange_state_create_lead(self):
    if self.state == 'deposit' and not self.crm_lead_id:
        lead = self.env['crm.lead'].create({
            'name': f"Сделка: {self.name}",
            'partner_id': self.owner_id.id,
            'expected_revenue': self.price,
            'user_id': self.user_id.id,
        })
        self.crm_lead_id = lead.id
```

---

## 2. Отслеживание участников для расчёта комиссии

### Проблема

По структуре ролей (docs/02_roles.md) комиссия распределяется между участниками:

| Роль | Оплата |
|------|--------|
| Team Lead | Остаток от комиссии |
| Listing Agent (VIP) | 25% |
| ISA Inbound | 100К + 3% |
| ISA Outbound | 100К + 5% |
| Listing Coordinator | 80К |
| Transaction Coordinator | 80К |
| Listing Agent | 15% |
| Buyer's Agent | 15% |

### Решение: фиксация участников в Odoo

В модели `estate.property` добавляем поля для отслеживания участников:

```python
class EstateProperty(models.Model):
    _name = "estate.property"

    # Кто внёс объект в базу (Listing Coordinator)
    listing_coordinator_id = fields.Many2one(
        'res.users',
        string="Внёс в базу",
        default=lambda self: self.env.user,
        tracking=True
    )
    listing_date = fields.Datetime(
        string="Дата внесения",
        default=fields.Datetime.now
    )

    # Кто ведёт объект (Listing Agent)
    listing_agent_id = fields.Many2one(
        'res.users',
        string="Листинг-агент",
        tracking=True
    )

    # Ответственный агент (может меняться)
    user_id = fields.Many2one(
        'res.users',
        string="Ответственный",
        tracking=True
    )
```

В расширении `crm.lead` добавляем поля для сделки:

```python
class CrmLead(models.Model):
    _inherit = "crm.lead"

    # Связь с объектом
    property_id = fields.Many2one(
        'estate.property',
        string="Объект"
    )

    # Кто квалифицировал лид (ISA)
    isa_user_id = fields.Many2one(
        'res.users',
        string="ISA (квалификация)",
        tracking=True
    )
    isa_date = fields.Datetime(
        string="Дата квалификации"
    )

    # Кто закрыл сделку (Buyer's Agent)
    buyer_agent_id = fields.Many2one(
        'res.users',
        string="Агент покупателя",
        tracking=True
    )

    # Кто вёл продавца (Listing Agent) — берётся из объекта
    listing_agent_id = fields.Many2one(
        related='property_id.listing_agent_id',
        string="Агент продавца",
        store=True
    )

    # Кто внёс объект в базу — берётся из объекта
    listing_coordinator_id = fields.Many2one(
        related='property_id.listing_coordinator_id',
        string="Внёс в базу",
        store=True
    )

    # Transaction Coordinator
    transaction_coordinator_id = fields.Many2one(
        'res.users',
        string="Координатор сделки",
        tracking=True
    )
```

### Данные для ERP

При закрытии сделки CRM передаёт в ERP:

```json
{
  "deal_id": 123,
  "deal_date": "2025-01-15",
  "property_id": 456,
  "price": 48000000,
  "commission": 1440000,
  "participants": {
    "listing_coordinator": {
      "user_id": 1,
      "action": "property_created",
      "date": "2024-12-01"
    },
    "isa": {
      "user_id": 2,
      "action": "lead_qualified",
      "date": "2024-12-15"
    },
    "listing_agent": {
      "user_id": 3,
      "action": "seller_management"
    },
    "buyer_agent": {
      "user_id": 4,
      "action": "deal_closed"
    },
    "transaction_coordinator": {
      "user_id": 5,
      "action": "documents_prepared"
    }
  }
}
```

### Логика: кто что получает

| Участник | За что платим | Откуда данные |
|----------|---------------|---------------|
| Listing Coordinator | Внёс объект в базу | `estate.property.listing_coordinator_id` |
| ISA | Квалифицировал лида | `crm.lead.isa_user_id` |
| Listing Agent | Вёл продавца | `estate.property.listing_agent_id` |
| Buyer's Agent | Закрыл сделку | `crm.lead.buyer_agent_id` |
| Transaction Coordinator | Подготовил документы | `crm.lead.transaction_coordinator_id` |
| Team Lead | Остаток | Рассчитывается в ERP |

---

## 3. ERP (Telegram бот) — расчёт зарплат

### API эндпоинты

ERP работает с **CRM сделками**, а не с объектами:

| Метод | Endpoint | Описание |
|-------|----------|----------|
| GET | `/api/v1/deals` | Список закрытых сделок |
| GET | `/api/v1/deals/{id}` | Детали сделки с участниками |
| GET | `/api/v1/deals/{id}/participants` | Участники сделки |
| GET | `/api/v1/users/{id}/deals` | Сделки сотрудника |
| GET | `/api/v1/stats/period` | Статистика за период |

### Авторизация

```
Authorization: Bearer <api_token>
```

### Пример запроса — закрытые сделки

```bash
curl -X GET "https://odoo.example.com/api/v1/deals?stage=won&date_from=2025-01-01" \
  -H "Authorization: Bearer abc123"
```

### Пример ответа

```json
{
  "count": 2,
  "deals": [
    {
      "id": 123,
      "name": "Сделка: 2-комн. квартира",
      "property_id": 456,
      "price": 48000000,
      "commission_total": 1440000,
      "stage": "won",
      "date_closed": "2025-01-15",
      "participants": {
        "listing_coordinator_id": 1,
        "isa_user_id": 2,
        "listing_agent_id": 3,
        "buyer_agent_id": 4,
        "transaction_coordinator_id": 5
      }
    }
  ]
}
```

### Webhooks из CRM в ERP

| Событие | Когда | Данные |
|---------|-------|--------|
| `deal.won` | Сделка закрыта | deal_id, participants, commission |
| `deal.participant_changed` | Изменён участник | deal_id, role, old_user_id, new_user_id |
| `property.created` | Создан объект | property_id, listing_coordinator_id |

```python
class CrmLead(models.Model):
    _inherit = "crm.lead"

    def _notify_erp_deal_won(self):
        """Уведомить ERP о закрытии сделки"""
        webhook_url = self.env['ir.config_parameter'].get_param('erp.webhook_url')
        if not webhook_url:
            return

        data = {
            'event': 'deal.won',
            'timestamp': fields.Datetime.now().isoformat(),
            'deal': {
                'id': self.id,
                'property_id': self.property_id.id,
                'price': self.expected_revenue,
                'date_closed': self.date_closed.isoformat(),
                'participants': {
                    'listing_coordinator_id': self.listing_coordinator_id.id,
                    'isa_user_id': self.isa_user_id.id,
                    'listing_agent_id': self.listing_agent_id.id,
                    'buyer_agent_id': self.buyer_agent_id.id,
                    'transaction_coordinator_id': self.transaction_coordinator_id.id,
                }
            }
        }
        requests.post(webhook_url, json=data)
```

---

## 4. 2GIS

### Виджет карты

```xml
<field name="map_widget" widget="estate_2gis_map"/>
```

### Геокодирование

```python
def _compute_coordinates(self):
    """Получить координаты по адресу через 2GIS API"""
    api_key = self.env['ir.config_parameter'].get_param('2gis.api_key')
    address = f"{self.street} {self.house_number}, Алматы"

    response = requests.get(
        "https://catalog.api.2gis.com/3.0/items/geocode",
        params={'q': address, 'key': api_key}
    )

    if response.ok:
        data = response.json()
        if data.get('result', {}).get('items'):
            point = data['result']['items'][0]['point']
            self.latitude = point['lat']
            self.longitude = point['lon']
```

### Поля координат

```python
latitude = fields.Float(string="Широта", digits=(10, 7))
longitude = fields.Float(string="Долгота", digits=(10, 7))
```

---

## 5. S3 Storage (фото)

### Архитектура

```
Загрузка фото
     │
     ▼
┌─────────────┐
│ Odoo        │──────▶ Миниатюра (Binary, 300x200)
│ Controller  │
└─────────────┘
     │
     ▼
┌─────────────┐
│ S3 Storage  │──────▶ Оригинал (до 10 МБ)
└─────────────┘
```

### Модель `estate.property.image`

| Поле | Тип | Описание |
|------|-----|----------|
| `property_id` | Many2one | Связь с объектом |
| `thumbnail` | Binary | Миниатюра 300x200 |
| `s3_url` | Char | URL оригинала в S3 |
| `s3_key` | Char | Ключ объекта в S3 |
| `sequence` | Integer | Порядок сортировки |
| `is_main` | Boolean | Главное фото |

### Водяные знаки

При экспорте фото накладывается водяной знак с логотипом агентства.

---

## 6. Матчинг (планируется)

### Концепция

Внешний сервис для автоматического подбора объектов под потребности покупателей.

### API матчинга

```
POST /api/v1/match
{
  "buyer_requirements": {
    "deal_type": "sale",
    "property_type": "apartment",
    "price_max": 50000000,
    "rooms_min": 2,
    "districts": ["medeu", "bostandyk"]
  },
  "limit": 10
}
```

### Интеграция с CRM

Результаты матчинга отображаются в карточке сделки (crm.lead) как рекомендуемые объекты.
