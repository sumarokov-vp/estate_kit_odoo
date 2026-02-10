# Архитектура хранения данных

## Проблема

У объекта недвижимости 50+ полей, большинство из которых:
- Опциональны (не заполняются для всех объектов)
- Зависят от типа объекта (квартира vs дом vs коммерция)
- Редко используются в фильтрах

Хранение всех полей в одной таблице приводит к:
- Разреженной таблице (много NULL значений)
- Сложности добавления новых характеристик
- Разным наборам полей для разных типов объектов

---

## Решение: EAV (Entity-Attribute-Value)

Разделяем данные на:
1. **Основная таблица** `estate.property` — минимум обязательных полей
2. **Справочник атрибутов** `estate.attribute` — описание характеристик
3. **Таблица значений** `estate.property.attribute.value` — значения характеристик

```
┌─────────────────────┐
│  estate.property    │
│  (основные поля)    │
│  ~15 колонок        │
└─────────┬───────────┘
          │ One2many
          ▼
┌─────────────────────────────┐      ┌─────────────────────┐
│  estate.property.attribute  │      │  estate.attribute   │
│  .value                     │─────▶│  (справочник)       │
│  (значения характеристик)   │      │  ~50 записей        │
└─────────────────────────────┘      └─────────────────────┘
```

---

## Сравнение подходов

| Критерий | Одна таблица | EAV |
|----------|--------------|-----|
| Разреженность | 50+ колонок, много NULL | Только заполненные значения |
| Добавление поля | ALTER TABLE | INSERT в справочник |
| Типо-зависимые поля | Сложно | Естественно |
| Фильтрация | Простая | Через JOIN |
| Производительность | Лучше для частых полей | Лучше для редких полей |

---

## Основная таблица `estate.property`

Только обязательные и часто используемые поля (~15):

| Поле | Тип | Описание |
|------|-----|----------|
| `name` | Char | Заголовок объявления |
| `property_type` | Selection | Тип объекта |
| `deal_type` | Selection | Тип сделки |
| `price` | Monetary | Цена |
| `currency_id` | Many2one | Валюта (KZT) |
| `rooms` | Integer | Количество комнат |
| `area_total` | Float | Общая площадь (м²) |
| `district_id` | Many2one | Район |
| `street` | Char | Улица |
| `house_number` | Char | Номер дома |
| `owner_id` | Many2one | Собственник (res.partner) |
| `user_id` | Many2one | Ответственный (res.users) |
| `state` | Selection | Стадия объекта |
| `attribute_value_ids` | One2many | Характеристики (EAV) |
| `image_ids` | One2many | Фотографии |

### Служебные поля

| Поле | Тип | Описание |
|------|-----|----------|
| `source_id` | Many2one | Источник клиента |
| `contract_type` | Selection | Тип договора |
| `contract_start` | Date | Дата начала договора |
| `contract_end` | Date | Дата окончания договора |
| `is_shared` | Boolean | Открытый объект |
| `internal_note` | Text | Внутренние заметки |
| `video_url` | Char | Ссылка на YouTube |
| `instagram_url` | Char | Ссылка на Instagram |

---

## Справочник атрибутов `estate.attribute`

| Поле | Тип | Описание |
|------|-----|----------|
| `name` | Char | Название атрибута |
| `code` | Char | Технический код |
| `field_type` | Selection | Тип данных |
| `category` | Selection | Категория (для группировки) |
| `property_types` | Char | Для каких типов объектов |
| `selection_options` | Text | Варианты для Selection (JSON) |
| `sequence` | Integer | Порядок сортировки |
| `is_filterable` | Boolean | Доступен в фильтрах |

### Типы данных (`field_type`)

| Код | Описание |
|-----|----------|
| `char` | Текст |
| `integer` | Целое число |
| `float` | Дробное число |
| `boolean` | Да/нет |
| `selection` | Выбор из списка |
| `date` | Дата |

### Категории (`category`)

| Код | Описание |
|-----|----------|
| `construction` | Характеристики строения |
| `area` | Площади |
| `utilities` | Коммуникации |
| `amenities` | Удобства |
| `security` | Безопасность |
| `legal` | Юридическое |

---

## Таблица значений `estate.property.attribute.value`

| Поле | Тип | Описание |
|------|-----|----------|
| `property_id` | Many2one | Объект недвижимости |
| `attribute_id` | Many2one | Атрибут |
| `value_char` | Char | Текстовое значение |
| `value_integer` | Integer | Числовое значение |
| `value_float` | Float | Дробное значение |
| `value_boolean` | Boolean | Булево значение |
| `value_selection` | Char | Код выбранного варианта |
| `value_date` | Date | Дата |

**SQL constraint:** `UNIQUE(property_id, attribute_id)`

---

## Пример данных

### Справочник атрибутов

| id | name | code | field_type | category | property_types |
|----|------|------|------------|----------|----------------|
| 1 | Этаж | floor | integer | construction | apartment |
| 2 | Этажность | floors_total | integer | construction | apartment |
| 3 | Год постройки | year_built | integer | construction | all |
| 4 | Тип строения | building_type | selection | construction | all |
| 5 | Жилая площадь | area_living | float | area | apartment,house |
| 6 | Площадь кухни | area_kitchen | float | area | apartment,house |
| 7 | Санузел | bathroom | selection | amenities | apartment,house |
| 8 | В залоге | is_pledged | boolean | legal | all |
| 9 | Домофон | security_intercom | boolean | security | apartment |

### Значения для объекта

| property_id | attribute_id | value_integer | value_boolean | value_selection |
|-------------|--------------|---------------|---------------|-----------------|
| 1 | 1 (Этаж) | 5 | | |
| 1 | 2 (Этажность) | 9 | | |
| 1 | 3 (Год постройки) | 2015 | | |
| 1 | 4 (Тип строения) | | | monolith |
| 1 | 8 (В залоге) | | false | |
| 1 | 9 (Домофон) | | true | |

---

## Работа с ORM Odoo

### Получение значения атрибута

```python
class EstateProperty(models.Model):
    _name = "estate.property"

    def get_attribute_value(self, code):
        """Получить значение атрибута по коду"""
        attr_value = self.attribute_value_ids.filtered(
            lambda v: v.attribute_id.code == code
        )
        if not attr_value:
            return None

        field_type = attr_value.attribute_id.field_type
        if field_type == 'integer':
            return attr_value.value_integer
        elif field_type == 'float':
            return attr_value.value_float
        elif field_type == 'boolean':
            return attr_value.value_boolean
        elif field_type == 'selection':
            return attr_value.value_selection
        elif field_type == 'date':
            return attr_value.value_date
        return attr_value.value_char
```

### Установка значения атрибута

```python
    def set_attribute_value(self, code, value):
        """Установить значение атрибута"""
        attribute = self.env['estate.attribute'].search([('code', '=', code)])
        if not attribute:
            return

        attr_value = self.attribute_value_ids.filtered(
            lambda v: v.attribute_id.code == code
        )

        field_name = f'value_{attribute.field_type}'
        vals = {'attribute_id': attribute.id, field_name: value}

        if attr_value:
            attr_value.write(vals)
        else:
            vals['property_id'] = self.id
            self.env['estate.property.attribute.value'].create(vals)
```

### Поиск объектов по атрибуту

```python
    def search_by_attribute(self, code, operator, value):
        """Поиск объектов по значению атрибута"""
        attribute = self.env['estate.attribute'].search([('code', '=', code)])
        field_name = f'value_{attribute.field_type}'

        attr_values = self.env['estate.property.attribute.value'].search([
            ('attribute_id', '=', attribute.id),
            (field_name, operator, value)
        ])
        return self.browse(attr_values.mapped('property_id.id'))
```

---

## Полный список атрибутов

См. [ATTRIBUTES.md](./ATTRIBUTES.md)
