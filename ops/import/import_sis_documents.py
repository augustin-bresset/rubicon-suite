"""
In-process SIS document loader: documents + items + FK resolution.

Run via odoo shell (env is provided), AFTER import_sis_parties.py:
    docker compose exec -T odoo odoo shell -d rubicon --no-http < ops/import/import_sis_documents.py

Steps:
  1. Wipe sis.document.item then sis.document (full reload).
  2. Bulk-load both from their CSVs via the generic importer (register_xml_id=False
     so 210k line items don't mint ir.model.data rows).
  3. Resolve FKs in-process (no XML-RPC): currency_legacy -> currency_id,
     design -> product_id (with /metal -> /W base fallback), party_code ->
     party_id (res.partner by sis_code), and child_doc_ids from item.ref_document.

Replaces import_sis_odoo + migrate_documents + build_child_docs.
"""
from collections import defaultdict

from odoo.addons.rubicon_import.import_scripts.generic import import_csv

Doc = env['sis.document']
Item = env['sis.document.item']

# ── 1. Wipe ────────────────────────────────────────────────────────────────
print("Clearing existing document items and documents...")
Item.search([]).unlink()
Doc.search([]).unlink()
env.cr.commit()
print("  => Tables cleared.")

# ── 2. Bulk load ───────────────────────────────────────────────────────────
print("Importing documents...")
import_csv(env, Doc, 'sis_document', register_xml_id=False)
env.cr.commit()
print("Importing document items...")
import_csv(env, Item, 'sis_document', register_xml_id=False)
env.cr.commit()
print("=== Bulk load done ===")

# ── 3a. Currency resolution ────────────────────────────────────────────────
CURRENCY_MAP = {
    'US$': 'USD', '$US': 'USD', 'US': 'USD', 'USD': 'USD',
    'EUR': 'EUR', 'EURO': 'EUR',
    'CHF': 'CHF', 'GBP': 'GBP', 'THB': 'THB',
    'HKD': 'HKD', 'YEN': 'JPY', 'JPY': 'JPY',
}
currency_by_name = {c.name.upper(): c.id for c in env['res.currency'].search([])}


def resolve_currency(legacy):
    if not legacy:
        return None
    val = legacy.strip().upper()
    return currency_by_name.get(CURRENCY_MAP.get(val, val))


print("Resolving document currencies...")
docs = Doc.search_read([('currency_legacy', '!=', False), ('currency_id', '=', False)],
                       ['id', 'currency_legacy'])
by_cur = defaultdict(list)
for d in docs:
    cid = resolve_currency(d['currency_legacy'])
    if cid:
        by_cur[cid].append(d['id'])
for cid, ids in by_cur.items():
    Doc.browse(ids).write({'currency_id': cid})
env.cr.commit()
print(f"  documents currency set: {sum(len(v) for v in by_cur.values())}/{len(docs)}")

# ── 3b. Product + currency resolution on items ─────────────────────────────
print("Loading PDP product codes...")
products = env['pdp.product'].search_read([('code', '!=', False)], ['id', 'code'])
product_by_code = {p['code'].strip().upper(): p['id'] for p in products}
# In PDP all products are stored under white gold (/W); strip a metal suffix.
product_by_base = {}
for p in products:
    code = p['code'].strip().upper()
    if '/' in code:
        product_by_base.setdefault(code.rsplit('/', 1)[0], p['id'])


def resolve_product(design):
    key = (design or '').strip().upper()
    if not key:
        return None
    if key in product_by_code:
        return product_by_code[key]
    if '/' in key:
        return product_by_base.get(key.rsplit('/', 1)[0])
    return None


print("Resolving item currencies + products...")
items = Item.search_read(['|', ('currency_id', '=', False), ('product_id', '=', False)],
                         ['id', 'currency_legacy', 'currency_id', 'design', 'product_id'])
items_by_vals = defaultdict(list)
unmapped_designs = set()
for it in items:
    vals = {}
    if it.get('currency_legacy') and not it.get('currency_id'):
        cid = resolve_currency(it['currency_legacy'])
        if cid:
            vals['currency_id'] = cid
    design = (it.get('design') or '').strip()
    if design and not it.get('product_id'):
        pid = resolve_product(design)
        if pid:
            vals['product_id'] = pid
        else:
            unmapped_designs.add(design.upper())
    if vals:
        items_by_vals[frozenset(vals.items())].append(it['id'])

items_updated = 0
for vals_tuple, ids in items_by_vals.items():
    vals = dict(vals_tuple)
    for i in range(0, len(ids), 5000):
        Item.browse(ids[i:i + 5000]).write(vals)
        items_updated += len(ids[i:i + 5000])
env.cr.commit()
print(f"  items scanned={len(items)} updated={items_updated} "
      f"unmapped_designs={len(unmapped_designs)}")

# ── 3c. Party link (party_code -> res.partner by sis_code) ─────────────────
print("Linking documents to parties by sis_code...")
partner_by_code = {
    p['sis_code']: p['id']
    for p in env['res.partner'].search_read(
        [('sis_code', '!=', False), ('is_company', '=', True)], ['id', 'sis_code'])
}
docs = Doc.search_read([('party_code', '!=', False)], ['id', 'party_code', 'party_id'])
by_partner = defaultdict(list)
for d in docs:
    pid = partner_by_code.get(d['party_code'])
    current = d['party_id'][0] if d['party_id'] else None
    if pid and pid != current:
        by_partner[pid].append(d['id'])
linked = 0
for pid, ids in by_partner.items():
    Doc.browse(ids).write({'party_id': pid})
    linked += len(ids)
env.cr.commit()
print(f"  documents linked to a party: {linked} (of {len(docs)} with a party_code)")

# ── 3d. Child documents (from item.ref_document) ───────────────────────────
print("Building parent->child document links...")
ref_items = Item.search_read([('ref_document', '!=', False)], ['document_id', 'ref_document'])
parent_to_children = defaultdict(set)
for it in ref_items:
    parent_name = (it['ref_document'] or '').strip()
    if parent_name and it['document_id']:
        parent_to_children[parent_name].add(it['document_id'][0])
child_updated = child_missing = 0
for parent_name, child_ids in parent_to_children.items():
    parent = Doc.search([('name', '=', parent_name)], limit=1)
    if parent:
        parent.write({'child_doc_ids': [(6, 0, list(child_ids))]})
        child_updated += 1
    else:
        child_missing += 1
env.cr.commit()
print(f"  parents updated={child_updated} parents_missing={child_missing}")

# ── Verification counts ────────────────────────────────────────────────────
print("\n=== SIS documents loaded ===")
for model in ['sis.document', 'sis.document.item']:
    print(f"  {model}: {env[model].search_count([])}")
print(f"  docs w/ currency_id : {Doc.search_count([('currency_id', '!=', False)])}")
print(f"  docs w/ party_id    : {Doc.search_count([('party_id', '!=', False)])}")
print(f"  items w/ product_id : {Item.search_count([('product_id', '!=', False)])}")
print(f"  items w/ currency_id: {Item.search_count([('currency_id', '!=', False)])}")
