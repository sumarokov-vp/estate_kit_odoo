# WhatsApp — отправка сообщений

## Архитектура

Odoo CRM отправляет сообщения клиентам через WhatsApp, публикуя события в RabbitMQ. Отдельный сервис **Meta WhatsApp Worker** потребляет сообщения из очереди и доставляет их через WhatsApp Cloud API.

```
┌──────────────┐     RabbitMQ      ┌──────────────┐     HTTPS      ┌──────────────┐
│   Odoo CRM   │──────────────────►│   WhatsApp   │──────────────►│  Meta Cloud  │
│              │  whatsapp.message  │    Worker    │               │     API      │
│              │      .send         │              │               │              │
└──────────────┘                    └──────────────┘               └──────────────┘
```

**Odoo не вызывает WhatsApp API напрямую.** Это позволяет:

- Не блокировать UI при отправке
- Автоматически повторять при сбоях (сообщения сохраняются в очереди)
- Контролировать rate limits (Meta ограничивает ~80 msg/sec на номер)

## Подключение к RabbitMQ

Odoo подключается к RabbitMQ-серверу, который работает рядом (на том же хосте или в docker-compose).

**Переменные окружения:**

| Переменная | Описание | Пример |
|---|---|---|
| `RABBITMQ_URL` | AMQP connection string | `amqp://estate_kit:estate_kit@rabbitmq:5672/` |

## Публикация сообщений

Для отправки WhatsApp-сообщения Odoo публикует событие в exchange `estate_kit.events` с routing key `whatsapp.message.send`.

### Exchange и очередь

| Параметр | Значение |
|---|---|
| Exchange | `estate_kit.events` |
| Exchange type | `topic` |
| Routing key | `whatsapp.message.send` |
| Queue | `whatsapp_messages` |

### Формат сообщения

Все сообщения — JSON с общей оберткой:

```json
{
  "event_id": "уникальный UUID события",
  "event_type": "whatsapp.message.send",
  "timestamp": "2026-03-30T12:00:00Z",
  "data": { ... }
}
```

### Типы сообщений

#### Текстовое сообщение

Свободный текст клиенту.

```json
{
  "event_id": "550e8400-e29b-41d4-a716-446655440000",
  "event_type": "whatsapp.message.send",
  "timestamp": "2026-03-30T12:00:00Z",
  "data": {
    "type": "text",
    "phone": "77001234567",
    "text": "Здравствуйте! Ваш объект по адресу ул. Абая 10 одобрен для публикации в MLS."
  }
}
```

| Поле | Тип | Обязательно | Описание |
|---|---|---|---|
| `type` | string | нет | `"text"` (по умолчанию) |
| `phone` | string | да | Номер телефона в международном формате без `+` |
| `text` | string | да | Текст сообщения (до 4096 символов) |

#### Шаблонное сообщение

Для отправки вне 24-часового окна диалога. Шаблоны предварительно создаются и одобряются в Meta Business Manager.

```json
{
  "event_id": "550e8400-e29b-41d4-a716-446655440001",
  "event_type": "whatsapp.message.send",
  "timestamp": "2026-03-30T12:00:00Z",
  "data": {
    "type": "template",
    "phone": "77001234567",
    "template_name": "property_approved",
    "language_code": "ru",
    "components": [
      {
        "type": "body",
        "parameters": [
          {"type": "text", "text": "ул. Абая 10"},
          {"type": "text", "text": "3-комнатная квартира"}
        ]
      }
    ]
  }
}
```

| Поле | Тип | Обязательно | Описание |
|---|---|---|---|
| `type` | string | да | `"template"` |
| `phone` | string | да | Номер телефона в международном формате без `+` |
| `template_name` | string | да | Имя шаблона из Meta Business Manager |
| `language_code` | string | нет | Код языка (по умолчанию `"ru"`) |
| `components` | array | нет | Параметры для подстановки в шаблон |

## Пример реализации в Odoo

### Публикация события

```python
import json
import uuid
from datetime import datetime, UTC

import pika


def send_whatsapp_message(rabbitmq_url: str, phone: str, text: str) -> None:
    """Опубликовать текстовое сообщение в очередь WhatsApp."""
    event = {
        "event_id": str(uuid.uuid4()),
        "event_type": "whatsapp.message.send",
        "timestamp": datetime.now(UTC).isoformat(),
        "data": {
            "type": "text",
            "phone": phone,
            "text": text,
        },
    }

    parameters = pika.URLParameters(rabbitmq_url)
    connection = pika.BlockingConnection(parameters)
    channel = connection.channel()

    channel.exchange_declare(
        exchange="estate_kit.events",
        exchange_type="topic",
        durable=True,
    )
    channel.basic_publish(
        exchange="estate_kit.events",
        routing_key="whatsapp.message.send",
        body=json.dumps(event).encode(),
        properties=pika.BasicProperties(content_type="application/json"),
    )
    connection.close()
```

### Отправка шаблонного сообщения

```python
def send_whatsapp_template(
    rabbitmq_url: str,
    phone: str,
    template_name: str,
    parameters: list[str],
) -> None:
    """Опубликовать шаблонное сообщение в очередь WhatsApp."""
    event = {
        "event_id": str(uuid.uuid4()),
        "event_type": "whatsapp.message.send",
        "timestamp": datetime.now(UTC).isoformat(),
        "data": {
            "type": "template",
            "phone": phone,
            "template_name": template_name,
            "language_code": "ru",
            "components": [
                {
                    "type": "body",
                    "parameters": [
                        {"type": "text", "text": p} for p in parameters
                    ],
                }
            ],
        },
    }

    parameters_rmq = pika.URLParameters(rabbitmq_url)
    connection = pika.BlockingConnection(parameters_rmq)
    channel = connection.channel()

    channel.exchange_declare(
        exchange="estate_kit.events",
        exchange_type="topic",
        durable=True,
    )
    channel.basic_publish(
        exchange="estate_kit.events",
        routing_key="whatsapp.message.send",
        body=json.dumps(event).encode(),
        properties=pika.BasicProperties(content_type="application/json"),
    )
    connection.close()
```

## Формат номера телефона

Номер указывается в международном формате **без символа `+`** и без пробелов/дефисов:

| Ввод пользователя | Формат для отправки |
|---|---|
| +7 700 123 45 67 | `77001234567` |
| 8 700 123 45 67 | `77001234567` |
| +7(700)123-45-67 | `77001234567` |

## Ограничения

- **24-часовое окно:** текстовые сообщения можно отправлять только если клиент писал в последние 24 часа. Вне окна — только шаблонные сообщения.
- **Rate limit:** ~80 сообщений в секунду на один номер отправителя (контролируется worker).
- **Шаблоны:** создаются и одобряются в Meta Business Manager вручную (обычно 1-2 рабочих дня).
