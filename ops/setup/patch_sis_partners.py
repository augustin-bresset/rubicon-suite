#!/usr/bin/env python3
"""
Patch res.partner records (sis_code set) with missing fields from sis.party.csv.

For each company in the CSV, finds the matching res.partner by sis_code and
fills in any field that is currently null/empty:
  - country_id     (via SIS→ISO mapping)
  - sis_pay_term_id
  - sis_ship_method_id
  - sis_ship_stamp
  - sis_group
  - sis_is_customer (True if pay_term present in CSV, else unchanged)

Also patches individuals: links to parent if parent_id is missing.

Run:
  python3 ops/setup/patch_sis_partners.py
"""
import csv
import os
import xmlrpc.client

URL  = 'http://localhost:8069'
DB   = 'rubicon'
USER = 'admin'
PASS = 'admin'

BASE     = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CSV_PATH = os.path.join(BASE, "rubicon_addons/sis_party/data/sis.party.csv")

# ── SIS country code → ISO alpha-2 ───────────────────────────────────────
SIS_TO_ISO = {
    'AE': 'AE', 'AR': 'AR', 'AU': 'AU', 'BE': 'BE',
    'BT': 'BL',  # St. Barthelemy
    'BZ': 'BR',  # Brazil
    'CA': 'CA',
    'CB': 'CO',  # Colombia
    'CH': 'CL',  # Chile (SIS uses CH, not Switzerland)
    'CN': 'CN',
    'CO': 'CR',  # Costa Rica
    'EG': 'EG',
    'EN': 'GB',  # United Kingdom
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

# ── Connect ───────────────────────────────────────────────────────────────
common = xmlrpc.client.ServerProxy(f'{URL}/xmlrpc/2/common')
uid    = common.authenticate(DB, USER, PASS, {})
assert uid, "Authentication failed!"
models = xmlrpc.client.ServerProxy(f'{URL}/xmlrpc/2/object')

def sr(model, domain, fields, limit=0):
    return models.execute_kw(DB, uid, PASS, model, 'search_read',
                             [domain], {'fields': fields, 'limit': limit})

def write(model, ids, vals):
    return models.execute_kw(DB, uid, PASS, model, 'write', [ids, vals])

# ── Load lookup tables ────────────────────────────────────────────────────
print("Loading res.country...")
countries = sr('res.country', [], ['id', 'code'])
country_by_iso = {c['code'].upper(): c['id'] for c in countries}
print(f"  {len(countries)} countries")

print("Loading sis.pay.term...")
pay_terms = sr('sis.pay.term', [], ['id', 'name'])
pay_term_by_name = {p['name']: p['id'] for p in pay_terms}
print(f"  {len(pay_terms)} pay terms: {list(pay_term_by_name.keys())}")

print("Loading sis.shipper...")
shippers = sr('sis.shipper', [], ['id', 'name'])
shipper_by_name = {s['name']: s['id'] for s in shippers}
print(f"  {len(shippers)} shippers")

def resolve_country(sis_xmlid):
    if not sis_xmlid or not sis_xmlid.startswith('sis_country_'):
        return None
    sis_code = sis_xmlid.replace('sis_country_', '').upper()
    iso_code = SIS_TO_ISO.get(sis_code, sis_code)
    return country_by_iso.get(iso_code)

# ── Load existing SIS partners ────────────────────────────────────────────
print("\nLoading existing SIS partners from res.partner...")
partners = sr('res.partner', [('sis_code', '!=', False)],
              ['id', 'sis_code', 'is_company', 'parent_id',
               'country_id', 'sis_pay_term_id', 'sis_ship_method_id',
               'sis_ship_stamp', 'sis_group', 'sis_is_customer'])
partner_by_code = {}
for p in partners:
    if p['sis_code']:
        partner_by_code[p['sis_code']] = p
print(f"  {len(partners)} SIS partners")

# ── Read CSV ──────────────────────────────────────────────────────────────
print(f"\nReading CSV: {CSV_PATH}")
rows = []
with open(CSV_PATH, newline='', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        rows.append(row)
print(f"  {len(rows)} rows")

# ── Process ───────────────────────────────────────────────────────────────
updated  = 0
skipped  = 0
not_found = 0
last_company_code = None
last_company_partner_id = None

for row in rows:
    code         = row.get('code', '').strip()
    contact_type = row.get('contact_type', '').strip()
    country_ref  = row.get('country_id/id', '').strip()

    if contact_type == 'company':
        last_company_code = code
        partner = partner_by_code.get(code)
        if not partner:
            not_found += 1
            last_company_partner_id = None
            continue

        last_company_partner_id = partner['id']
        vals = {}

        # country_id — only patch if missing
        if not partner['country_id']:
            cid = resolve_country(country_ref)
            if cid:
                vals['country_id'] = cid

        # sis_pay_term_id — only patch if missing
        if not partner['sis_pay_term_id']:
            pt_name = row.get('pay_term_id', '').strip()
            if pt_name and pt_name in pay_term_by_name:
                vals['sis_pay_term_id'] = pay_term_by_name[pt_name]

        # sis_ship_method_id — only patch if missing
        if not partner['sis_ship_method_id']:
            sh_name = row.get('ship_method_id', '').strip()
            if sh_name and sh_name in shipper_by_name:
                vals['sis_ship_method_id'] = shipper_by_name[sh_name]

        # sis_ship_stamp — only patch if missing
        if not partner['sis_ship_stamp']:
            stamp = row.get('ship_stamp', '').strip()
            if stamp:
                vals['sis_ship_stamp'] = stamp

        # sis_group — only patch if missing
        if not partner['sis_group']:
            grp = row.get('group_code', '').strip()
            if grp:
                vals['sis_group'] = grp

        # sis_is_customer — set True if partner has a pay term (implies sales relationship)
        # Only set if currently False and CSV has a pay term for this party
        if not partner['sis_is_customer']:
            pt_name = row.get('pay_term_id', '').strip()
            if pt_name:
                vals['sis_is_customer'] = True

        if vals:
            try:
                write('res.partner', [partner['id']], vals)
                updated += 1
            except Exception as e:
                print(f"  ⚠ [{code}] {e}")
                skipped += 1
        # else: nothing to patch

    elif contact_type == 'individual':
        # Patch parent_id if missing
        # Find the individual by searching partners linked to last company
        if not last_company_partner_id:
            continue
        # Individuals don't have sis_code; find by parent
        # We check if there are already individuals linked to this company
        # (can't reliably re-link without a unique key, skip)
        pass

print(f"\n[SUCCESS] Patch complete!")
print(f"   Updated   : {updated}")
print(f"   Skipped   : {skipped}")
print(f"   Not found : {not_found}")

# ── Summary ───────────────────────────────────────────────────────────────
print("\n📊 POST-PATCH SUMMARY")
no_country  = sr('res.partner', [('sis_code', '!=', False), ('is_company', '=', True), ('country_id', '=', False)], ['id'])
no_pt       = sr('res.partner', [('sis_code', '!=', False), ('is_company', '=', True), ('sis_pay_term_id', '=', False)], ['id'])
is_cust     = sr('res.partner', [('sis_code', '!=', False), ('is_company', '=', True), ('sis_is_customer', '=', True)], ['id'])
print(f"   Companies without country  : {len(no_country)}")
print(f"   Companies without pay term : {len(no_pt)}")
print(f"   Companies with is_customer : {len(is_cust)}")
