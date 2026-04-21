#!/usr/bin/env python3
"""
Sync sis.party.csv → res.partner (UPDATE only, never creates duplicates).

For each company row in the CSV, finds the existing partner by sis_code and
writes ALL address/contact/SIS fields from the new CSV format.

Run:
  python3 ops/setup/sync_parties.py
  python3 ops/setup/sync_parties.py --dry-run
"""
import csv
import os
import re
import sys
import xmlrpc.client

DRY_RUN = '--dry-run' in sys.argv

URL  = 'http://localhost:8069'
DB   = 'rubicon'
USER = 'admin'
PASS = 'admin'

BASE     = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CSV_PATH = os.path.join(BASE, 'rubicon_addons/sis_party/data/sis.party.csv')

common = xmlrpc.client.ServerProxy(f'{URL}/xmlrpc/2/common')
uid    = common.authenticate(DB, USER, PASS, {})
assert uid, "Authentication failed!"
models = xmlrpc.client.ServerProxy(f'{URL}/xmlrpc/2/object')

def sr(model, domain, fields, limit=0):
    return models.execute_kw(DB, uid, PASS, model, 'search_read',
                             [domain], {'fields': fields, 'limit': limit})

def do_write(model, ids, vals):
    if DRY_RUN:
        return True
    return models.execute_kw(DB, uid, PASS, model, 'write', [ids, vals])

# ── Lookup tables ─────────────────────────────────────────────────────────
print("Loading lookup tables...")

countries = sr('res.country', [], ['id', 'name'])
country_by_name = {c['name'].upper(): c['id'] for c in countries}

pay_terms = sr('sis.pay.term', [], ['id', 'name'])
pay_term_by_name = {p['name']: p['id'] for p in pay_terms}

shippers = sr('sis.shipper', [], ['id', 'name'])
shipper_by_name = {s['name']: s['id'] for s in shippers}

margins = sr('pdp.margin', [], ['id', 'code'])
margin_by_code = {m['code']: m['id'] for m in margins}

def resolve_country(name):
    return country_by_name.get((name or '').strip().upper())

# ── Existing SIS partners indexed by sis_code ─────────────────────────────
print("Loading existing SIS partners...")
partners = sr('res.partner', [('sis_code', '!=', False), ('is_company', '=', True)],
              ['id', 'sis_code'])
partner_by_code = {p['sis_code']: p['id'] for p in partners}
print(f"  {len(partner_by_code)} company partners found")

# ── Read CSV ──────────────────────────────────────────────────────────────
print(f"Reading {CSV_PATH}...")
rows = []
with open(CSV_PATH, newline='', encoding='utf-8') as f:
    for row in csv.DictReader(f):
        rows.append(row)
print(f"  {len(rows)} rows")

# ── Sync ──────────────────────────────────────────────────────────────────
updated   = 0
not_found = 0
skipped   = 0

EMAIL_RE = re.compile(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z]{2,}')

for row in rows:
    code = row.get('sis_code', '').strip()
    if not code or row.get('is_company', '').strip() != 'True':
        continue

    partner_id = partner_by_code.get(code)
    if not partner_id:
        not_found += 1
        continue

    vals = {}

    # ── Address ───────────────────────────────────────────────────────────
    for f in ('street', 'street2', 'city', 'zip'):
        v = row.get(f, '').strip()
        if v and v not in ('NA', '0', '1'):
            vals[f] = v

    cid = resolve_country(row.get('country_id', ''))
    if cid:
        vals['country_id'] = cid

    # ── Contact ───────────────────────────────────────────────────────────
    phone = row.get('phone', '').strip()
    if phone:
        vals['phone'] = phone
    mobile = row.get('mobile', '').strip()
    if mobile:
        vals['mobile'] = mobile
    email = row.get('email', '').strip()
    if email and EMAIL_RE.search(email):
        vals['email'] = email
    website = row.get('website', '').strip()
    if website:
        vals['website'] = website
    notes = row.get('notes', '').strip()
    if notes:
        vals['comment'] = notes

    # ── SIS fields ────────────────────────────────────────────────────────
    sis_contact = row.get('sis_contact', '').strip()
    if sis_contact:
        vals['sis_contact'] = sis_contact
    vals['sis_is_customer'] = row.get('sis_is_customer', '').strip() == 'True'
    vals['sis_is_vendor']   = row.get('sis_is_vendor', '').strip() == 'True'

    margin_code = row.get('margin_id', '').strip()
    if margin_code in margin_by_code:
        vals['margin_id'] = margin_by_code[margin_code]

    pay_term = row.get('sis_pay_term_id', '').strip()
    if pay_term in pay_term_by_name:
        vals['sis_pay_term_id'] = pay_term_by_name[pay_term]

    ship_method = row.get('sis_ship_method_id', '').strip()
    if ship_method in shipper_by_name:
        vals['sis_ship_method_id'] = shipper_by_name[ship_method]

    # ── Shipment ──────────────────────────────────────────────────────────
    fedex = row.get('sis_ship_fedex_acc', '').strip()
    if fedex:
        vals['sis_ship_fedex_acc'] = fedex
    ship_city = row.get('sis_ship_city', '').strip()
    if ship_city:
        vals['sis_ship_city'] = ship_city
    ship_zip = row.get('sis_ship_zip', '').strip()
    if ship_zip:
        vals['sis_ship_zip'] = ship_zip
    ship_cid = resolve_country(row.get('sis_ship_country_id', ''))
    if ship_cid:
        vals['sis_ship_country_id'] = ship_cid
    stamp = row.get('sis_ship_stamp', '').strip()
    if stamp:
        vals['sis_ship_stamp'] = stamp

    if not vals:
        skipped += 1
        continue

    try:
        do_write('res.partner', [partner_id], vals)
        updated += 1
        if DRY_RUN and updated <= 3:
            print(f"  [DRY] [{code}] would write: { {k: v for k, v in vals.items() if k in ('city','zip','country_id','phone')} }")
    except Exception as e:
        print(f"  Error [{code}]: {e}")
        skipped += 1

print(f"\n{'[DRY RUN] ' if DRY_RUN else ''}Done!")
print(f"  Updated   : {updated}")
print(f"  Not found : {not_found}")
print(f"  Skipped   : {skipped}")
