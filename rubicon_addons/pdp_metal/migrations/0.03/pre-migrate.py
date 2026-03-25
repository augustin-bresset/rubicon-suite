"""
Pre-migration: register external IDs for reference data records.

On databases where records were created without going through the module's
CSV files (no ir.model.data entries), upgrades fail with a unique constraint
error because Odoo tries INSERT instead of UPDATE.

This script runs before data files are loaded, registers the external IDs with
noupdate=True so the CSV loader will skip (not overwrite) them on upgrade.
"""


def migrate(cr, version):
    cr.execute("""
        INSERT INTO ir_model_data (name, model, module, res_id, noupdate)
        SELECT 'metal_' || code, 'pdp.metal', 'pdp_metal', id, true
        FROM metals
        ON CONFLICT (module, name) DO NOTHING;
    """)

    cr.execute("""
        INSERT INTO ir_model_data (name, model, module, res_id, noupdate)
        SELECT 'purity_' || code, 'pdp.metal.purity', 'pdp_metal', id, true
        FROM pdp_metal_purity
        ON CONFLICT (module, name) DO NOTHING;
    """)

    cr.execute("""
        INSERT INTO ir_model_data (name, model, module, res_id, noupdate)
        SELECT 'part_' || REPLACE(REPLACE(code, '.', '_'), ' ', '_'),
               'pdp.part', 'pdp_metal', id, true
        FROM pdp_part
        ON CONFLICT (module, name) DO NOTHING;
    """)
