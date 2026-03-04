from odoo.addons.rubicon_import.import_scripts.generic import import_csv

# Import documents (15,969 records)
print("Starting documents import...")
import_csv(env, env['sis.document'], 'sis_document')
env.cr.commit()
print("=== Documents done ===")

# Import document items (210,474 records)
print("Starting items import...")
import_csv(env, env['sis.document.item'], 'sis_document')
env.cr.commit()
print("=== Document Items done ===")

# Verification counts
for model_name in ['sis.region', 'sis.country', 'sis.pay.term', 'sis.shipper',
                    'sis.trade.fair', 'sis.party', 'sis.doc.type', 'sis.doc.in.mode',
                    'sis.document', 'sis.document.item']:
    count = env[model_name].search_count([])
    print(f"  {model_name}: {count} records")

print("\n=== ALL SIS IMPORTS COMPLETE ===")
