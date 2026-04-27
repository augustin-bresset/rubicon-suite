#!/usr/bin/env python3
"""
Migrate party data from cleaned sis.party.csv into res.partner.

Reads the cleaned CSV and creates res.partner records via XML-RPC:
- Companies → company_type='company' with SIS fields
- Individuals → company_type='person' linked to parent company

Also re-links sis.document.party_id references.
"""
import csv
import os
import re
import xmlrpc.client

URL = 'http://localhost:8069'
DB = 'rubicon'
USER = 'admin'
PASS = 'admin'

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

def create(model, vals):
    return models.execute_kw(DB, uid, PASS, model, 'create', [vals])

def write(model, ids, vals):
    return models.execute_kw(DB, uid, PASS, model, 'write', [ids, vals])

# --- Country lookup: Odoo name → res.country ID ---
print("Loading res.country mapping...")
countries = search_read('res.country', [], ['id', 'name'])
country_by_name = {c['name'].upper(): c['id'] for c in countries}
print(f"  {len(countries)} countries available")

def resolve_country(name):
    """Resolve Odoo res.country name → ID (case-insensitive)."""
    if not name:
        return None
    return country_by_name.get(name.strip().upper())

# --- Load pay terms, shippers and margins for reference ---
pay_terms = search_read('sis.pay.term', [], ['id', 'name'])
pay_term_by_name = {p['name']: p['id'] for p in pay_terms}

shippers = search_read('sis.shipper', [], ['id', 'name'])
shipper_by_name = {s['name']: s['id'] for s in shippers}

margins = search_read('pdp.margin', [], ['id', 'code'])
margin_by_code = {m['code']: m['id'] for m in margins}

EMAIL_RE = re.compile(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z]{2,}')
PHONE_RE = re.compile(r'^[\+\d][\d\s\-\(\)\.]{6,}$')

# --- Read CSV ---
print(f"Reading CSV: {CSV_PATH}")
rows = []
with open(CSV_PATH, newline='', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        rows.append(row)
print(f"  {len(rows)} rows")

# --- Process ---
created_companies = 0
skipped = 0
sis_code_to_partner_id = {}  # SIS code → new partner ID
last_company_partner_id = None
last_company_sis_code = None

for row in rows:
    # New CSV field names (as of raw_to_data_sis.py refactor)
    code         = row.get('sis_code', '').strip()
    company_name = row.get('name', '').strip()
    is_company   = row.get('is_company', '').strip() == 'True'

    if not company_name:
        skipped += 1
        continue

    if is_company:
        vals = {
            'name': company_name,
            'company_type': 'company',
            'is_company': True,
            'sis_code': code,
        }

        # Address
        street = row.get('street', '').strip()
        if street:
            vals['street'] = street
        street2 = row.get('street2', '').strip()
        if street2 and street2 not in ('1', '0', 'NA'):
            vals['street2'] = street2
        city = row.get('city', '').strip()
        if city:
            vals['city'] = city
        zip_val = row.get('zip', '').strip()
        if zip_val:
            vals['zip'] = zip_val

        # Country: CSV now holds the Odoo res.country name (e.g. "United States")
        country_id = resolve_country(row.get('country_id', ''))
        if country_id:
            vals['country_id'] = country_id

        # Communication
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

        # Notes
        notes = row.get('notes', '').strip()
        if notes:
            vals['comment'] = notes

        # SIS identity
        sis_contact = row.get('sis_contact', '').strip()
        if sis_contact:
            vals['sis_contact'] = sis_contact
        vals['sis_is_customer'] = row.get('sis_is_customer', '').strip() == 'True'
        vals['sis_is_vendor']   = row.get('sis_is_vendor', '').strip() == 'True'

        # Margin: CSV holds pdp.margin code (_rec_name='code'), e.g. "WHO"
        margin_code = row.get('margin_id', '').strip()
        if margin_code and margin_code in margin_by_code:
            vals['margin_id'] = margin_by_code[margin_code]

        pay_term = row.get('sis_pay_term_id', '').strip()
        if pay_term and pay_term in pay_term_by_name:
            vals['sis_pay_term_id'] = pay_term_by_name[pay_term]

        ship_method = row.get('sis_ship_method_id', '').strip()
        if ship_method and ship_method in shipper_by_name:
            vals['sis_ship_method_id'] = shipper_by_name[ship_method]

        # Shipment details
        fedex_acc = row.get('sis_ship_fedex_acc', '').strip()
        if fedex_acc:
            vals['sis_ship_fedex_acc'] = fedex_acc
        ship_city = row.get('sis_ship_city', '').strip()
        if ship_city:
            vals['sis_ship_city'] = ship_city
        ship_zip = row.get('sis_ship_zip', '').strip()
        if ship_zip:
            vals['sis_ship_zip'] = ship_zip
        ship_country_id = resolve_country(row.get('sis_ship_country_id', ''))
        if ship_country_id:
            vals['sis_ship_country_id'] = ship_country_id

        stamp = row.get('sis_ship_stamp', '').strip()
        if stamp:
            vals['sis_ship_stamp'] = stamp

        try:
            partner_id = create('res.partner', vals)
            sis_code_to_partner_id[code] = partner_id
            last_company_partner_id = partner_id
            last_company_sis_code = code
            created_companies += 1
        except Exception as e:
            print(f"  Error creating company [{code}] {company_name}: {e}")
            skipped += 1

print(f"\n[SUCCESS] Migration complete!")
print(f"   Companies created: {created_companies}")
print(f"   Skipped:           {skipped}")

# --- Re-link documents ---
print(f"\n=== Re-linking sis.document.party_id ===")
docs = search_read('sis.document', [('party_code', '!=', False)], ['id', 'party_code'])
linked = 0
for doc in docs:
    party_code = doc['party_code']
    partner_id = sis_code_to_partner_id.get(party_code)
    if partner_id:
        write('sis.document', [doc['id']], {'party_id': partner_id})
        linked += 1

print(f"   Documents re-linked: {linked}/{len(docs)}")
print(f"\n[SUCCESS] All done!")
