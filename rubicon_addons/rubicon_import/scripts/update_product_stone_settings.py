# scripts/update_product_stone_settings.py
# Updates pdp.product.stone with setting_type_id from the regenerated CSV.
# Run via:  odoo shell -d rubicon < scripts/update_product_stone_settings.py

from odoo.addons.rubicon_import.import_scripts.generic import import_csv

import_csv(env, env['pdp.product.stone'], module='pdp_product')
env.cr.commit()
print("[SUCCESS] pdp.product.stone setting_type_id updated.")
