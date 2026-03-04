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

# --- Country mapping: SIS code → res.country ID ---
print("Loading res.country mapping...")
countries = search_read('res.country', [], ['id', 'code', 'name'])
country_by_code = {}
for c in countries:
    country_by_code[c['code'].upper()] = c['id']
print(f"  {len(countries)} countries available")

# SIS custom codes → ISO codes
SIS_TO_ISO = {
    'AE': 'AE', 'AR': 'AR', 'AU': 'AU', 'BE': 'BE',
    'BT': 'BL',  # St. Barthelemy
    'BZ': 'BR',  # Brazil
    'CA': 'CA',
    'CB': 'CO',  # Colombia
    'CH': 'CL',  # Chile (SIS used CH for Chile, not Switzerland)
    'CN': 'CN', 'CO': 'CR',  # Costa Rica
    'EG': 'EG',
    'EN': 'GB',  # UK
    'FR': 'FR',
    'GM': 'DE',  # Germany
    'GR': 'GR',
    'HD': 'HN',  # Honduras
    'HK': 'HK',
    'HO': 'NL',  # Holland → Netherlands
    'IN': 'ID',  # Indonesia
    'IS': 'IL',  # Israel
    'IT': 'IT', 'JP': 'JP', 'KR': 'KR',
    'ME': 'MX',  # Mexico
    'ML': 'MY',  # Malaysia
    'NC': 'NC', 'NL': 'NL', 'NZ': 'NZ', 'RU': 'RU',
    'SA': 'ZA',  # South Africa
    'SG': 'SG',
    'SP': 'ES',  # Spain
    'SU': 'SA',  # Saudi Arabia
    'SW': 'CH',  # Switzerland
    'TA': 'TZ',  # Tanzania
    'TH': 'TH',
    'TU': 'TR',  # Turkey
    'TW': 'TW',
    'UK': 'UA',  # Ukraine
    'US': 'US', 'VE': 'VE',
}

def resolve_country(sis_xmlid):
    """Resolve sis_country_XX → res.country ID."""
    if not sis_xmlid or not sis_xmlid.startswith('sis_country_'):
        return None
    sis_code = sis_xmlid.replace('sis_country_', '').upper()
    iso_code = SIS_TO_ISO.get(sis_code, sis_code)
    return country_by_code.get(iso_code)

# --- Load pay terms and shippers for reference ---
pay_terms = search_read('sis.pay.term', [], ['id', 'name'])
pay_term_by_name = {p['name']: p['id'] for p in pay_terms}

shippers = search_read('sis.shipper', [], ['id', 'name'])
shipper_by_name = {s['name']: s['id'] for s in shippers}

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
created_individuals = 0
skipped = 0
sis_code_to_partner_id = {}  # SIS code → new partner ID
last_company_partner_id = None
last_company_sis_code = None

for row in rows:
    code = row.get('code', '').strip()
    company_name = row.get('company', '').strip()
    contact_type = row.get('contact_type', '').strip()
    country_ref = row.get('country_id/id', '').strip()

    if contact_type == 'company':
        # Build company partner vals
        vals = {
            'name': company_name,
            'company_type': 'company',
            'is_company': True,
            'sis_code': code,
        }

        # Address
        addr = row.get('address', '').strip()
        if addr and addr not in ('1', '0', 'NA'):
            vals['street'] = addr
        city = row.get('city', '').strip()
        if city:
            vals['city'] = city
        state = row.get('state', '').strip()
        if state:
            vals['state_id'] = False  # We won't try to resolve state
        zip_val = row.get('zip', '').strip()
        if zip_val:
            vals['zip'] = zip_val

        # Country
        country_id = resolve_country(country_ref)
        if country_id:
            vals['country_id'] = country_id

        # Communication
        phone = row.get('phone', '').strip()
        if phone and PHONE_RE.match(phone):
            vals['phone'] = phone
        fax = row.get('fax', '').strip()
        # No fax field in res.partner, skip
        email = row.get('email', '').strip()
        if email and EMAIL_RE.search(email):
            vals['email'] = email
        homepage = row.get('homepage', '').strip()
        if homepage:
            vals['website'] = homepage

        # Notes
        notes = row.get('notes', '').strip()
        if notes:
            vals['comment'] = notes

        # SIS specifics
        group = row.get('group_code', '').strip()
        if group:
            vals['sis_group'] = group
        account = row.get('account', '').strip()
        if account:
            vals['sis_account'] = account

        pay_term = row.get('pay_term_id', '').strip()
        if pay_term and pay_term in pay_term_by_name:
            vals['sis_pay_term_id'] = pay_term_by_name[pay_term]

        ship_method = row.get('ship_method_id', '').strip()
        if ship_method and ship_method in shipper_by_name:
            vals['sis_ship_method_id'] = shipper_by_name[ship_method]

        stamp = row.get('ship_stamp', '').strip()
        if stamp:
            vals['sis_ship_stamp'] = stamp

        try:
            partner_id = create('res.partner', vals)
            sis_code_to_partner_id[code] = partner_id
            last_company_partner_id = partner_id
            last_company_sis_code = code
            created_companies += 1
        except Exception as e:
            print(f"  ⚠ Error creating company [{code}] {company_name}: {e}")
            skipped += 1

    elif contact_type == 'individual':
        # Individual: just name, linked to parent
        vals = {
            'name': company_name,  # 'company' field in CSV = person name
            'company_type': 'person',
            'is_company': False,
        }

        if last_company_partner_id:
            vals['parent_id'] = last_company_partner_id

        try:
            partner_id = create('res.partner', vals)
            created_individuals += 1
        except Exception as e:
            print(f"  ⚠ Error creating individual {company_name}: {e}")
            skipped += 1

print(f"\n✅ Migration complete!")
print(f"   Companies created:    {created_companies}")
print(f"   Individuals created:  {created_individuals}")
print(f"   Skipped:              {skipped}")

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
print(f"\n✅ All done!")
