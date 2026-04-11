# scripts/reimport_product_stones.py
# Deletes ALL pdp.product.stone records and reimports from CSV with XML IDs.
# Run via:  odoo shell -d rubicon < scripts/reimport_product_stones.py

from odoo.addons.rubicon_import.import_scripts.generic import import_csv

print("[INFO] Deleting all pdp.product.stone records...")
all_stones = env['pdp.product.stone'].search([])
count_before = len(all_stones)
all_stones.unlink()
print(f"[INFO] Deleted {count_before} records.")
env.cr.commit()

print("[INFO] Reimporting pdp.product.stone from CSV (no XML IDs)...")
import_csv(env, env['pdp.product.stone'], module='pdp_product', register_xml_id=False)
env.cr.commit()
print("[SUCCESS] pdp.product.stone reimported with setting_type_id.")
