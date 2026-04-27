"""
Post-import script: build sis.document child_doc_ids relationships.

Uses already-imported sis.document.item records (ref_document field) to derive
parent→child links. No access to raw CSV files needed — runs entirely in Odoo.

Run after import_sis_odoo.py:
    docker compose exec -T odoo odoo shell -d rubicon --no-http < ops/import/build_child_docs.py
"""

print("Building parent→child document mapping from sis.document.item...")

# Fetch all items that reference a parent document
items = env['sis.document.item'].search([('ref_document', '!=', False)])
print(f"  => Items with ref_document: {len(items)}")

# Build {parent_name: set of child document ids}
parent_to_child_ids = {}
for item in items:
    parent_name = (item.ref_document or '').strip()
    child_id    = item.document_id.id
    if parent_name and child_id:
        parent_to_child_ids.setdefault(parent_name, set()).add(child_id)

print(f"  => Distinct parent document names: {len(parent_to_child_ids)}")

SisDoc = env['sis.document']
updated = 0
missing = 0

for parent_name, child_ids in parent_to_child_ids.items():
    parent = SisDoc.search([('name', '=', parent_name)], limit=1)
    if not parent:
        missing += 1
        continue
    parent.write({'child_doc_ids': [(6, 0, list(child_ids))]})
    updated += 1

env.cr.commit()

print(f"  => Updated  : {updated} parent documents")
print(f"  => Missing  : {missing} parent names not found in DB")
print("=== Child document relationships done ===")
