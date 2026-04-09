def migrate(cr, version):
    if not version:
        return
    cr.execute("""
        ALTER TABLE estate_lead_match
        DROP CONSTRAINT IF EXISTS estate_lead_match_property_id_fkey;

        ALTER TABLE estate_lead_match
        ADD CONSTRAINT estate_lead_match_property_id_fkey
        FOREIGN KEY (property_id)
        REFERENCES estate_property(id)
        ON DELETE CASCADE;
    """)
