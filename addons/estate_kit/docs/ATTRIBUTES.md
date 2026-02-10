# Справочник атрибутов

Полный список атрибутов объектов недвижимости, сгруппированных по категориям.

**Обозначения типов объектов:**
- `A` — Квартира (apartment)
- `H` — Дом (house)
- `C` — Коммерция (commercial)
- `L` — Земля (land)
- `*` — Все типы

---

## Характеристики строения (`construction`)

| Код | Название | Тип | Объекты | Варианты |
|-----|----------|-----|---------|----------|
| `floor` | Этаж | integer | A, C | — |
| `floors_total` | Этажность | integer | A, H, C | — |
| `year_built` | Год постройки | integer | * | — |
| `building_type` | Тип строения | selection | A, H | panel, brick, monolith, block |
| `ceiling_height` | Высота потолков | float | A, H, C | — |
| `entrance` | Подъезд | integer | A | — |
| `wall_material` | Материал стен | selection | H | brick, block, wood, sip, frame |
| `roof_type` | Тип крыши | selection | H | flat, gable, hip |
| `foundation` | Фундамент | selection | H | strip, slab, pile |

---

## Площади (`area`)

| Код | Название | Тип | Объекты | Единица |
|-----|----------|-----|---------|---------|
| `area_living` | Жилая площадь | float | A, H | м² |
| `area_kitchen` | Площадь кухни | float | A, H | м² |
| `area_land` | Площадь участка | float | H, L | сотки |
| `area_commercial` | Торговая площадь | float | C | м² |
| `area_warehouse` | Складская площадь | float | C | м² |

---

## Удобства (`amenities`)

| Код | Название | Тип | Объекты | Варианты |
|-----|----------|-----|---------|----------|
| `bathroom` | Санузел | selection | A, H | combined, separate, two_plus |
| `balcony` | Балкон | selection | A | none, balcony, loggia |
| `balcony_glazed` | Балкон застеклён | boolean | A | — |
| `parking` | Парковка | selection | * | none, yard, underground, garage |
| `furniture` | Мебель | selection | A, H | none, partial, full |
| `condition` | Состояние | selection | A, H, C | no_repair, cosmetic, euro, designer |

---

## Коммуникации (`utilities`)

| Код | Название | Тип | Объекты | Варианты |
|-----|----------|-----|---------|----------|
| `heating` | Отопление | selection | * | central, autonomous, none |
| `water` | Водоснабжение | selection | H, L | central, well, none |
| `sewage` | Канализация | selection | H, L | central, septic, none |
| `gas` | Газ | selection | H, L | central, balloon, none |
| `electricity` | Электричество | selection | H, L | yes, nearby, none |
| `internet` | Интернет | boolean | A, H, C | — |

---

## Безопасность (`security`)

| Код | Название | Тип | Объекты |
|-----|----------|-----|---------|
| `security_intercom` | Домофон | boolean | A |
| `security_alarm` | Сигнализация | boolean | * |
| `security_guard` | Охрана | boolean | A, C |
| `security_video` | Видеонаблюдение | boolean | * |
| `security_coded_lock` | Кодовый замок | boolean | A |
| `security_bars` | Решётки на окнах | boolean | A |

---

## Особенности (`features`)

| Код | Название | Тип | Объекты |
|-----|----------|-----|---------|
| `plastic_windows` | Пластиковые окна | boolean | A, H |
| `air_conditioning` | Кондиционер | boolean | A, H, C |
| `meters` | Счётчики | boolean | A, H |
| `not_corner` | Не угловая | boolean | A |
| `isolated_rooms` | Изолированные комнаты | boolean | A |
| `storage` | Кладовка | boolean | A |
| `quiet_yard` | Тихий двор | boolean | A |
| `kitchen_studio` | Кухня-студия | boolean | A |
| `new_plumbing` | Новая сантехника | boolean | A, H |
| `built_in_kitchen` | Встроенная кухня | boolean | A, H |

---

## Юридическое (`legal`)

| Код | Название | Тип | Объекты |
|-----|----------|-----|---------|
| `is_pledged` | В залоге | boolean | * |
| `is_privatized` | Приватизирована | boolean | A |
| `documents_ready` | Документы готовы | boolean | * |
| `ownership_type` | Тип собственности | selection | * |
| `encumbrance` | Обременение | boolean | * |

**Варианты `ownership_type`:**
- `private` — Частная собственность
- `shared` — Долевая собственность
- `state` — Государственная

---

## Коммерческая недвижимость (`commercial`)

| Код | Название | Тип | Объекты | Варианты |
|-----|----------|-----|---------|----------|
| `commercial_type` | Назначение | selection | C | office, retail, warehouse, production |
| `has_showcase` | Витрины | boolean | C | — |
| `separate_entrance` | Отдельный вход | boolean | C | — |
| `ceiling_height_com` | Высота потолков | float | C | — |
| `electricity_power` | Мощность электричества | integer | C | кВт |

---

## Земельные участки (`land`)

| Код | Название | Тип | Объекты | Варианты |
|-----|----------|-----|---------|----------|
| `land_category` | Категория земли | selection | L | izhs, snt, lpkh, commercial |
| `land_status` | Статус | selection | L | owned, leased |
| `communications_nearby` | Коммуникации рядом | boolean | L | — |
| `road_access` | Подъездная дорога | selection | L | asphalt, gravel, dirt, none |

**Варианты `land_category`:**
- `izhs` — ИЖС
- `snt` — СНТ
- `lpkh` — ЛПХ
- `commercial` — Коммерческое назначение

---

## Итого по категориям

| Категория | Количество атрибутов |
|-----------|---------------------|
| Характеристики строения | 9 |
| Площади | 5 |
| Удобства | 6 |
| Коммуникации | 6 |
| Безопасность | 6 |
| Особенности | 10 |
| Юридическое | 5 |
| Коммерция | 5 |
| Земля | 4 |
| **Всего** | **56** |
