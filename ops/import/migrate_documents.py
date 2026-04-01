#!/usr/bin/env python3
"""
Migrate sis.document and sis.document.item in BATCES:
1. currency_legacy -> res.currency ID
2. design -> pdp.product ID
"""
import os
import xmlrpc.client
from collections import defaultdict

URL = 'http://localhost:8069'
DB = 'rubicon'
USER = 'admin'
PASS = 'admin'

# --- Connect ---
common = xmlrpc.client.ServerProxy(f'{URL}/xmlrpc/2/common')
uid = common.authenticate(DB, USER, PASS, {})
assert uid, "Authentication failed!"
models = xmlrpc.client.ServerProxy(f'{URL}/xmlrpc/2/object')

def search_read(model, domain, fields, limit=0):
    return models.execute_kw(DB, uid, PASS, model, 'search_read',
                             [domain], {'fields': fields, 'limit': limit})

def write(model, ids, vals):
    return models.execute_kw(DB, uid, PASS, model, 'write', [ids, vals])

# --- Fetch Reference Data ---
print("Fetching currencies...")
currencies = search_read('res.currency', [], ['id', 'name'])
currency_by_name = {c['name'].upper(): c['id'] for c in currencies}

print("Fetching PDP products...")
products = search_read('pdp.product', [], ['id', 'code'])
product_by_code = {p['code'].strip().upper(): p['id'] for p in products if p.get('code')}

# Normalize currency strings from legacy data to iso
CURRENCY_MAP = {
    'US$': 'USD', '$US': 'USD', 'USD': 'USD',
    'EUR': 'EUR', 'EURO': 'EUR',
    'CHF': 'CHF', 'GBP': 'GBP', 'THB': 'THB',
    'HKD': 'HKD', 'YEN': 'JPY', 'JPY': 'JPY',
}

def resolve_currency(legacy_str):
    if not legacy_str:
        return None
    val = legacy_str.strip().upper()
    iso = CURRENCY_MAP.get(val, val)
    return currency_by_name.get(iso)

# --- 1. Migrate Documents ---
print("\n=== Migrating Documents ===")
docs = search_read('sis.document', [('currency_legacy', '!=', False), ('currency_id', '=', False)], ['id', 'currency_legacy'])
docs_by_currency = defaultdict(list)

for doc in docs:
    currency_id = resolve_currency(doc['currency_legacy'])
    if currency_id:
        docs_by_currency[currency_id].append(doc['id'])

doc_updated = 0
for currency_id, doc_ids in docs_by_currency.items():
    write('sis.document', doc_ids, {'currency_id': currency_id})
    doc_updated += len(doc_ids)

print(f"Documents updated: {doc_updated}")

# --- 2. Migrate Items ---
print("\n=== Migrating Document Items ===")
# Only read items that lack either currency or product
items = search_read('sis.document.item', ['|', ('currency_id', '=', False), ('product_id', '=', False)], 
                    ['id', 'currency_legacy', 'currency_id', 'design', 'product_id'])

# Group queries by unique update values
items_by_vals = defaultdict(list)
items_skipped_no_product = set()

for item in items:
    v = {}
    if item.get('currency_legacy') and not item.get('currency_id'):
        currency_id = resolve_currency(item['currency_legacy'])
        if currency_id:
            v['currency_id'] = currency_id
            
    design = item.get('design', '').strip().upper()
    if design and not item.get('product_id'):
        product_id = product_by_code.get(design)
        if product_id:
            v['product_id'] = product_id
        else:
            items_skipped_no_product.add(design)
            
    if v:
        # Convert dict to a hashable tuple of items so we can group identical updates
        key = frozenset(v.items())
        items_by_vals[key].append(item['id'])

items_updated = 0
# Send batched writes
for vals_tuple, item_ids in items_by_vals.items():
    vals_dict = dict(vals_tuple)
    # limit batch size to 5000 per XML-RPC call
    for i in range(0, len(item_ids), 5000):
        batch = item_ids[i:i+5000]
        write('sis.document.item', batch, vals_dict)
        items_updated += len(batch)

print(f"Items updated with bulk queries: {items_updated}")
print(f"Total Items scanned matching condition: {len(items)}")

if items_skipped_no_product:
    print(f"Could not map {len(items_skipped_no_product)} unique designs to PDP products.")

print("\n[SUCCESS] Migration complete!")
