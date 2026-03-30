---
name: crm-stages
description: Управление стадиями CRM лида. Добавление, удаление, переименование стадий. Используй когда нужно изменить pipeline стадий в CRM.
allowed-tools: Read, Edit, Write, Bash, Glob, Grep
---

Управление стадиями CRM лида. $ARGUMENTS

## Контекст

CRM лид в Odoo проходит через pipeline стадий (statusbar). Стадии определяются в таблице `crm.stage`. У нас кастомный pipeline — переходы только через action-кнопки, клик по statusbar отключён.

### Текущий pipeline

Стандартные стадии Odoo (модуль `crm`):
- `crm.stage_lead1` — Новое (sequence 1)
- `crm.stage_lead3` — Предложение (sequence 6)
- `crm.stage_lead4` — Выиграно (sequence 70)

Кастомные стадии Estate Kit (`addons/estate_kit/data/crm_stages.xml`):
- `estate_kit.crm_stage_matched` — Подобрано (sequence 3)
- `estate_kit.crm_stage_viewing` — Просмотр (sequence 4)
- `estate_kit.crm_stage_negotiation` — Переговоры (sequence 5)
- `estate_kit.crm_stage_lost` — Потеряно (sequence 80, fold)

Удалённые стадии:
- `crm.stage_lead2` — Квалифицирован (удалена в миграции 19.0.1.7.3)

## Операции

### Добавление стадии

1. Добавить `<record>` в `addons/estate_kit/data/crm_stages.xml` (внутри `<odoo noupdate="1">`):
   ```xml
   <record id="crm_stage_<name>" model="crm.stage">
       <field name="name">Название</field>
       <field name="sequence">N</field>
   </record>
   ```
   - `sequence` определяет порядок в statusbar (меньше = левее)
   - Опциональные поля: `fold` (свёрнутая в kanban), `is_won` (стадия победы)

2. Файл `noupdate="1"` — новые записи создаются при установке модуля, но **не обновляются** при upgrade. Для существующих инсталляций нужна **миграция**.

3. Если стадия используется в кнопках или логике — добавить action-метод в модель и кнопку в `crm_lead_views.xml`.

### Удаление стадии

**Стадии нельзя просто удалить из XML** — `noupdate="1"` не удалит записи при upgrade, а лиды могут ссылаться на стадию.

1. **Создать миграцию** `post-migrate.py`:
   - Переместить все лиды из удаляемой стадии в целевую (обычно первую)
   - Удалить запись из `ir_model_data`
   - Удалить запись из `crm_stage`

   Шаблон:
   ```python
   import logging
   _logger = logging.getLogger(__name__)

   def migrate(cr, version):
       if not version:
           return

       # Найти стадию по xmlid
       cr.execute(
           "SELECT res_id FROM ir_model_data "
           "WHERE module = %s AND name = %s AND model = 'crm.stage'",
           ("estate_kit", "crm_stage_<name>"),  # или ("crm", "stage_lead<N>")
       )
       row = cr.fetchone()
       if not row:
           return

       stage_id = row[0]

       # Переместить лиды в целевую стадию
       cr.execute(
           "SELECT res_id FROM ir_model_data "
           "WHERE module = 'crm' AND name = 'stage_lead1' AND model = 'crm.stage'"
       )
       target_id = cr.fetchone()[0]
       cr.execute(
           "UPDATE crm_lead SET stage_id = %s WHERE stage_id = %s",
           (target_id, stage_id),
       )

       # Удалить стадию
       cr.execute(
           "DELETE FROM ir_model_data WHERE res_id = %s AND model = 'crm.stage'",
           (stage_id,),
       )
       cr.execute("DELETE FROM crm_stage WHERE id = %s", (stage_id,))
       _logger.info("Deleted stage id=%s", stage_id)
   ```

2. **Поднять версию** в `__manifest__.py` (например `19.0.1.7.3` → `19.0.1.7.4`).

3. Создать папку миграции: `migrations/<новая_версия>/post-migrate.py`.

4. Убрать `<record>` из `crm_stages.xml` (необязательно для работы, но для чистоты).

5. Убрать связанные кнопки из `crm_lead_views.xml` и action-методы из моделей.

### Переименование стадии

Из-за `noupdate="1"` переименование через XML не сработает при upgrade. Нужна миграция:

```python
import json

def migrate(cr, version):
    if not version:
        return
    cr.execute(
        "SELECT res_id FROM ir_model_data "
        "WHERE module = %s AND name = %s AND model = 'crm.stage'",
        ("estate_kit", "crm_stage_<name>"),
    )
    row = cr.fetchone()
    if row:
        name = json.dumps({"en_US": "New Name", "ru_RU": "Новое название"})
        cr.execute("UPDATE crm_stage SET name = %s WHERE id = %s", (name, row[0]))
```

## Важные особенности

- **Нет поля `active`**: у `crm.stage` в Odoo 19 нет `active` — стадии можно только удалять, не архивировать.
- **`noupdate="1"`**: изменения в `crm_stages.xml` применяются только при первой установке. Для обновления существующих БД — всегда миграция.
- **Стандартные стадии Odoo** (`crm.stage_lead*`) — их xmlid принадлежит модулю `crm`, не `estate_kit`. При удалении указывать `module='crm'`.
- **Кнопки в header**: динамические кнопки привязаны к стадиям через `invisible="stage_id != %(xmlid)d"` в `crm_lead_views.xml`.

## Ключевые файлы

- `addons/estate_kit/data/crm_stages.xml` — определение стадий
- `addons/estate_kit/views/crm_lead_views.xml` — кнопки и statusbar
- `addons/estate_kit/src/lead/models/crm_lead_matching.py` — action-методы переходов
- `addons/estate_kit/__manifest__.py` — версия модуля
- `addons/estate_kit/migrations/` — миграции
