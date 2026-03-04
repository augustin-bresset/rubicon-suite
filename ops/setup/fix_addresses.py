#!/usr/bin/env python3
"""
Fix street addresses on res.partner by reading the raw backup CSV.

The raw CustomersClean.csv has:
  [4] Add1 = street number (or "NA"/"0")
  [5] Add2 = street name
  [6] Add3 = extra address line

This script combines them into res.partner.street / street2.
"""
import csv
import io
import os
import xmlrpc.client

URL = 'http://localhost:8069'
DB = 'rubicon'
USER = 'admin'
PASS = 'admin'

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
RAW_CSV = os.path.join(BASE, "data/backup_sis/CustomersClean.csv")

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

# --- Load existing partners by sis_code ---
print("Loading res.partner records...")
partners = search_read('res.partner', [('sis_code', '!=', False)], ['id', 'sis_code', 'name'])
partner_by_code = {p['sis_code']: p['id'] for p in partners}
print(f"  {len(partners)} SIS partners loaded")

# --- Read raw CSV ---
print(f"Reading raw CSV: {RAW_CSV}")
with open(RAW_CSV, encoding='utf-8', errors='replace') as f:
    lines = f.readlines()
print(f"  {len(lines)} lines")

updated = 0
not_found = 0

for line in lines:
    line = line.strip()
    if not line:
        continue

    # Parse CSV line
    reader = csv.reader(io.StringIO(line))
    try:
        fields = next(reader)
    except:
        continue

    # Skip individual rows (1 field = just a name)
    if len(fields) < 10:
        continue

    code = fields[1].strip()
    add1 = fields[4].strip()
    add2 = fields[5].strip()
    add3 = fields[6].strip() if len(fields) > 6 else ''

    # Find partner
    partner_id = partner_by_code.get(code)
    if not partner_id:
        not_found += 1
        continue

    # Build street address
    # Add1: if it's a real number, combine with Add2 as "number, street"
    # If Add1 is "NA", "0", empty, or already included in Add2, just use Add2
    street = ''
    street2 = ''

    is_number = add1.isdigit() or (add1.replace('-', '').isdigit())
    is_skip = add1 in ('', 'NA', '0', 'N/A')

    if add2:
        if is_number and add1 != '0':
            street = f"{add1}, {add2}"
        elif is_skip:
            street = add2
        else:
            # Add1 is something else (like an actual address part)
            street = f"{add1} {add2}".strip()
    elif add1 and not is_skip:
        street = add1

    if add3:
        street2 = add3

    vals = {}
    if street:
        vals['street'] = street
    if street2:
        vals['street2'] = street2

    if vals:
        # Sanitize: remove null bytes and XML-incompatible chars
        for k, v in vals.items():
            if isinstance(v, str):
                vals[k] = v.replace('\x00', '').replace('\0', '')
        try:
            write('res.partner', [partner_id], vals)
            updated += 1
        except Exception as e:
            print(f"  ⚠ [{code}] Error: {e}"[:100])

print(f"\n✅ Done!")
print(f"   Updated:   {updated}")
print(f"   Not found: {not_found}")

# Show samples
print(f"\n📍 SAMPLES:")
samples = search_read('res.partner', [('sis_code', 'in', ['EMA', 'Z&Z', 'KOZ', 'BAL', 'STE'])],
                       ['sis_code', 'name', 'street', 'street2', 'city', 'zip', 'country_id'])
for s in samples:
    country = s['country_id'][1] if s['country_id'] else 'N/A'
    print(f"  [{s['sis_code']}] {s['name']}")
    print(f"       street:  {s['street'] or '-'}")
    print(f"       street2: {s['street2'] or '-'}")
    print(f"       city:    {s['city'] or '-'}  zip: {s['zip'] or '-'}  country: {country}")
