from odoo import SUPERUSER_ID, api


def migrate(cr, version):
    if not version:
        return

    env = api.Environment(cr, SUPERUSER_ID, {})

    # 1. plastic_windows -> window_type
    cr.execute("""
        UPDATE estate_property
        SET window_type = 'plastic'
        WHERE plastic_windows = true
    """)

    # 2. internet boolean -> selection
    # В PostgreSQL bool колонка будет преобразована в selection
    # Сначала добавляем временную колонку если нужно
    cr.execute("""
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'estate_property'
                AND column_name = 'internet'
                AND data_type = 'boolean'
            ) THEN
                ALTER TABLE estate_property
                RENAME COLUMN internet TO internet_old;

                ALTER TABLE estate_property
                ADD COLUMN internet VARCHAR;

                UPDATE estate_property
                SET internet = 'wired'
                WHERE internet_old = true;

                ALTER TABLE estate_property
                DROP COLUMN internet_old;
            END IF;
        END $$;
    """)

    # 3. building_type 'block' -> NULL
    cr.execute("""
        UPDATE estate_property
        SET building_type = NULL
        WHERE building_type = 'block'
    """)

    # 4. wall_material 'block' -> 'gas_block'
    cr.execute("""
        UPDATE estate_property
        SET wall_material = 'gas_block'
        WHERE wall_material = 'block'
    """)

    # 5. air_conditioning -> climate_equipment_ids
    # Находим ID записи "Кондиционер" в справочнике
    air_conditioner = env["estate.climate.equipment"].search(
        [("code", "=", "air_conditioner")], limit=1
    )

    if air_conditioner:
        # Получаем все объекты с air_conditioning=True
        cr.execute("""
            SELECT id FROM estate_property
            WHERE air_conditioning = true
        """)
        property_ids = [row[0] for row in cr.fetchall()]

        if property_ids:
            # Получаем имя таблицы связи many2many
            # По умолчанию Odoo создаёт таблицу:
            # estate_property_estate_climate_equipment_rel
            relation_table = "estate_property_estate_climate_equipment_rel"

            # Проверяем существование таблицы
            cr.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_name = %s
                )
            """, (relation_table,))

            if cr.fetchone()[0]:
                # Вставляем связи
                for property_id in property_ids:
                    cr.execute(f"""
                        INSERT INTO {relation_table}
                        (estate_property_id, estate_climate_equipment_id)
                        VALUES (%s, %s)
                        ON CONFLICT DO NOTHING
                    """, (property_id, air_conditioner.id))
