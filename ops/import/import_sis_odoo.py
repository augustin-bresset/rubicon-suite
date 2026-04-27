from odoo.addons.rubicon_import.import_scripts.generic import import_csv

# Full reload: wipe existing data to avoid duplicates on re-run
print("Clearing existing document items and documents...")
env['sis.document.item'].search([]).unlink()
env['sis.document'].search([]).unlink()
env.cr.commit()
print("  => Tables cleared.")

# Import documents
print("Starting documents import...")
import_csv(env, env['sis.document'], 'sis_document', register_xml_id=True)
env.cr.commit()
print("=== Documents done ===")

# Import document items
print("Starting items import...")
import_csv(env, env['sis.document.item'], 'sis_document', register_xml_id=True)
env.cr.commit()
print("=== Document Items done ===")

# Verification counts
for model_name in ['sis.pay.term', 'sis.shipper', 'sis.trade.fair',
                    'sis.doc.type', 'sis.doc.in.mode',
                    'sis.document', 'sis.document.item']:
    count = env[model_name].search_count([])
    print(f"  {model_name}: {count} records")

print("\n=== ALL SIS IMPORTS COMPLETE ===")
