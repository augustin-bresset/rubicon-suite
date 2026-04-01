#!/usr/bin/env python3
"""
Populate contact_type, is_company, parent_id, and country_id
on existing sis.party records using the cleaned CSV as source of truth.

Uses XML-RPC to update records in Odoo.
"""
import csv
import os
import xmlrpc.client

URL = 'http://localhost:8069'
DB = 'rubicon'
USER = 'admin'
PASS = 'admin'

# Resolve paths relative to project root (two levels up from ops/import/)
BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CSV_PATH = os.path.join(BASE, "rubicon_addons/sis_party/data/sis.party.csv")

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

# --- Load country lookup from Odoo ---
print("Loading countries from Odoo...")
countries = search_read('sis.country', [], ['id', 'code', 'name'])
country_by_code = {}
for c in countries:
    country_by_code[c['code'].upper()] = c['id']
    country_by_code[c['name'].upper()] = c['id']
print(f"  {len(countries)} countries, {len(country_by_code)} lookup entries")

# --- Get XML ID → Odoo ID mapping for countries ---
# sis_country_FR → code FR → Odoo ID
def resolve_country_xmlid(xmlid):
    """e.g. 'sis_country_FR' -> look up by code 'FR'."""
    if not xmlid or not xmlid.startswith('sis_country_'):
        return None
    code = xmlid.replace('sis_country_', '').upper()
    return country_by_code.get(code)

# --- Load CSV ---
print(f"Reading CSV: {CSV_PATH}")
rows = []
with open(CSV_PATH, newline='', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        rows.append(row)
print(f"  {len(rows)} rows in CSV")

# --- Get all parties from Odoo ---
print("Fetching existing parties from Odoo...")
all_parties = search_read('sis.party', [], ['id', 'code', 'company'])
print(f"  {len(all_parties)} parties in Odoo")

# Build lookups
party_by_key = {}
for p in all_parties:
    key = (p['code'] or '', p['company'] or '')
    party_by_key[key] = p['id']

party_by_code = {}
for p in all_parties:
    if p['code'] and p['code'] != '0':
        party_by_code[p['code']] = p['id']

# --- Process CSV rows ---
updated = 0
skipped = 0
not_found = 0
parent_linked = 0
country_set = 0
last_company_code = None

for row in rows:
    code = row.get('code', '').strip()
    company = row.get('company', '').strip()
    contact_type = row.get('contact_type', '').strip()
    is_company = row.get('is_company', '').strip() == 'True'
    country_ref = row.get('country_id/id', '').strip()

    # Find Odoo record
    key = (code, company)
    odoo_id = party_by_key.get(key)
    if not odoo_id:
        if code and code != '0':
            odoo_id = party_by_code.get(code)
        if not odoo_id:
            not_found += 1
            continue

    vals = {}
    if contact_type:
        vals['contact_type'] = contact_type
    vals['is_company'] = is_company

    # Resolve country_id
    if country_ref:
        country_odoo_id = resolve_country_xmlid(country_ref)
        if country_odoo_id:
            vals['country_id'] = country_odoo_id
            country_set += 1

    # Track company for parent linking
    if contact_type == 'company':
        last_company_code = code

    # Link individual to parent company
    if contact_type == 'individual' and last_company_code:
        parent_odoo_id = party_by_code.get(last_company_code)
        if parent_odoo_id:
            vals['parent_id'] = parent_odoo_id
            parent_linked += 1

    if vals:
        try:
            write('sis.party', [odoo_id], vals)
            updated += 1
        except Exception as e:
            print(f"  ⚠ Error updating [{code}] {company}: {e}")
            skipped += 1

print(f"\n[SUCCESS] Done!")
print(f"   Updated:       {updated}")
print(f"   Parent links:  {parent_linked}")
print(f"   Country set:   {country_set}")
print(f"   Skipped:       {skipped}")
print(f"   Not found:     {not_found}")
