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

print("Loading res.country.state...")
states = sr('res.country.state', [], ['id', 'code', 'country_id'])
state_by_country_code = {
    (s['country_id'][0], s['code'].upper()): s['id']
    for s in states
}
print(f"  {len(states)} states loaded")

def resolve_state(state_code, country_odoo_id):
    if not state_code or not country_odoo_id:
        return None
    return state_by_country_code.get((country_odoo_id, state_code.strip().upper()))

# ── Existing SIS partners indexed by sis_code ─────────────────────────────
print("Loading existing SIS partners...")
partners = sr('res.partner', [('sis_code', '!=', False), ('is_company', '=', True)],
              ['id', 'sis_code'])
partner_by_code = {p['sis_code']: p['id'] for p in partners}
print(f"  {len(partner_by_code)} company partners found")

print("Loading existing child partners (delivery + contact)...")
children = sr('res.partner',
              [('type', 'in', ['delivery', 'contact']),
               ('parent_id', 'in', list(partner_by_code.values()))],
              ['id', 'type', 'parent_id'])

delivery_by_parent = {}
contact_by_parent  = {}
contact_dups_to_delete = []
for c in children:
    pid = c['parent_id'][0]
    if c['type'] == 'delivery':
        delivery_by_parent[pid] = c['id']
    elif c['type'] == 'contact':
        if pid in contact_by_parent:
            contact_dups_to_delete.append(c['id'])
        else:
            contact_by_parent[pid] = c['id']

if contact_dups_to_delete and not DRY_RUN:
    models.execute_kw(DB, uid, PASS, 'res.partner', 'unlink', [contact_dups_to_delete])
    print(f"  Removed {len(contact_dups_to_delete)} duplicate contact children")
print(f"  {len(delivery_by_parent)} delivery, {len(contact_by_parent)} contacts found")

print("Loading existing bank accounts...")
banks = sr('res.partner.bank',
           [('partner_id', 'in', list(partner_by_code.values()))],
           ['id', 'partner_id'])
bank_by_partner = {b['partner_id'][0]: b['id'] for b in banks}
print(f"  {len(bank_by_partner)} bank accounts found")

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

    company_name = row.get('name', '').strip()
    vals = {}

    # ── Address ───────────────────────────────────────────────────────────
    for f in ('street', 'street2', 'city', 'zip'):
        v = row.get(f, '').strip()
        if v and v not in ('NA', '0', '1'):
            vals[f] = v

    cid = resolve_country(row.get('country_id', ''))
    if cid:
        vals['country_id'] = cid

    state_code = row.get('state_code', '').strip()
    cid_for_state = vals.get('country_id') or resolve_country(row.get('country_id', ''))
    sid = resolve_state(state_code, cid_for_state)
    if sid:
        vals['state_id'] = sid

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
            print(f"  [DRY] [{code}] would write: { {k: v for k, v in vals.items() if k in ('city','zip','country_id','phone','state_id')} }")
    except Exception as e:
        print(f"  Error [{code}]: {e}")
        skipped += 1
        continue

    # ── Delivery child (type='delivery') ─────────────────────────────────────
    ship_country_id = resolve_country(row.get('sis_ship_country_id', ''))
    ship_state_id   = resolve_state(row.get('sis_ship_state_code', ''), ship_country_id)
    ship_city = row.get('sis_ship_city', '').strip()
    ship_zip  = row.get('sis_ship_zip', '').strip()

    if ship_city or ship_country_id:
        delivery_vals = {
            'type': 'delivery',
            'parent_id': partner_id,
            'name': company_name,
        }
        if ship_city:
            delivery_vals['city'] = ship_city
        if ship_zip:
            delivery_vals['zip'] = ship_zip
        if ship_country_id:
            delivery_vals['country_id'] = ship_country_id
        if ship_state_id:
            delivery_vals['state_id'] = ship_state_id

        existing_delivery = delivery_by_parent.get(partner_id)
        if existing_delivery:
            do_write('res.partner', [existing_delivery], delivery_vals)
        else:
            if DRY_RUN:
                print(f"  [DRY] [{code}] would create delivery child: {delivery_vals.get('city')}, {delivery_vals.get('zip')}")
            else:
                new_id = models.execute_kw(DB, uid, PASS, 'res.partner', 'create', [delivery_vals])
                delivery_by_parent[partner_id] = new_id

    # ── Contact child (type='contact') ────────────────────────────────────────
    contact_name = row.get('sis_contact', '').strip()
    if contact_name:
        contact_vals = {
            'type': 'contact',
            'parent_id': partner_id,
            'name': contact_name,
            'is_company': False,
        }
        existing_contact = contact_by_parent.get(partner_id)
        if existing_contact:
            do_write('res.partner', [existing_contact], contact_vals)
        else:
            if DRY_RUN:
                print(f"  [DRY] [{code}] would create contact child: {contact_name}")
            else:
                new_id = models.execute_kw(DB, uid, PASS, 'res.partner', 'create', [contact_vals])
                contact_by_parent[partner_id] = new_id

    # ── Bank account (res.partner.bank) ───────────────────────────────────────
    bank_acc_no = row.get('bank_acc_no', '').strip()
    bank_name   = row.get('bank_name', '').strip()
    if bank_acc_no or bank_name:
        bank_vals = {
            'partner_id':     partner_id,
            'acc_number':     bank_acc_no or '—',
            'acc_holder_name': row.get('bank_acc_name', '').strip(),
            'sis_bank_name':  bank_name,
            'sis_bank_address': row.get('bank_address', '').strip(),
        }
        existing_bank = bank_by_partner.get(partner_id)
        if existing_bank:
            do_write('res.partner.bank', [existing_bank], bank_vals)
        else:
            if not DRY_RUN:
                new_id = models.execute_kw(DB, uid, PASS, 'res.partner.bank', 'create', [bank_vals])
                bank_by_partner[partner_id] = new_id

print(f"\n{'[DRY RUN] ' if DRY_RUN else ''}Done!")
print(f"  Updated   : {updated}")
print(f"  Not found : {not_found}")
print(f"  Skipped   : {skipped}")
