"""
Post-import script: build sis.document child_doc_ids relationships.

In the legacy SIS, invoice (SI) items reference their parent sales order via
ref_document (the SO doc name). This script reads SalesDocItems.csv, derives
the parent→child mapping, then writes the Many2many on each parent document.

Run after import_sis_odoo.py:
    docker compose exec -T odoo odoo shell -d rubicon --no-http < ops/import/build_child_docs.py
"""
import csv
import os

backup = '/home/smaug/rubicon-suite/data/backup_sis'

print("Building parent→child document mapping from SalesDocItems.csv...")

# {parent_doc_name: set of child_doc_names}
parent_to_children = {}

items_path = os.path.join(backup, 'SalesDocItems.csv')
docs_path  = os.path.join(backup, 'SalesDocs.csv')

# Build doc lookup: (doc_type, legacy_id) → doc_name
doc_name_lookup = {}
with open(docs_path, encoding='utf-8') as f:
    for row in csv.reader(f):
        if len(row) >= 4:
            dt = row[0].strip()
            lid = row[1].strip()
            name = row[3].strip()
            if dt and lid and name:
                doc_name_lookup[(dt, lid)] = name

# Scan items for ref_document links
with open(items_path, encoding='utf-8') as f:
    for row in csv.reader(f):
        if len(row) < 6:
            continue
        doc_type  = row[0].strip()
        legacy_id = row[1].strip()
        ref_doc   = row[5].strip()
        if not ref_doc:
            continue
        child_name = doc_name_lookup.get((doc_type, legacy_id))
        if not child_name or child_name == ref_doc:
            continue
        parent_to_children.setdefault(ref_doc, set()).add(child_name)

print(f"  => Found {len(parent_to_children)} parent documents with children")

# Apply relationships in Odoo
SisDoc = env['sis.document']
updated = 0
missing_parent = 0
missing_child  = 0

for parent_name, child_names in parent_to_children.items():
    parent = SisDoc.search([('name', '=', parent_name)], limit=1)
    if not parent:
        missing_parent += 1
        continue

    children = SisDoc.search([('name', 'in', list(child_names))])
    found_names = set(children.mapped('name'))
    missing_child += len(child_names - found_names)

    if children:
        parent.write({'child_doc_ids': [(6, 0, children.ids)]})
        updated += 1

env.cr.commit()

print(f"  => Updated  : {updated} parent documents")
print(f"  => Missing parents  : {missing_parent}")
print(f"  => Missing children : {missing_child}")
print("=== Child document relationships done ===")
