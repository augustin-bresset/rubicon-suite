from odoo.addons.rubicon_import.import_scripts.generic import import_csv

print("Clearing existing SIS partners...")
env['res.partner'].search([('sis_code', '!=', False)]).unlink()
env.cr.commit()
print("  => SIS partners cleared.")

print("Starting partner import...")
import_csv(env, env['res.partner'], 'sis_party', register_xml_id=True,
           csv_path='/mnt/extra-addons/sis_party/data/sis.party.csv')
env.cr.commit()
print("=== Partners done ===")

count = env['res.partner'].search_count([('sis_code', '!=', False)])
print(f"  res.partner (sis_code set): {count} records")
