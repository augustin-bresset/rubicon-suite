#!/usr/bin/env python3
"""
Fix field interpretation errors in SIS res.partner records:

  1. website = phone number (e.g. "http://52 333 641 1423")
     → clear website, add to sis_phone_ids as "Phone 2"

  2. city = 2-letter US / AU state code (e.g. "FL", "NSW")
     → move to state_id, city = ''
     (more complete than fix_partner_city_state.py — also handles AU states)

  3. Contact rows in sis.party.csv carry shipment address + bank info
     packed into wrong columns. Extract and write to:
       - sis_ship_address, sis_ship_country_id (from city / email cols)
       - bank_ids (from notes / group_code cols)
     Only if those fields are currently empty on the company.

DRY-RUN by default. Pass --apply to execute.

Run:
  python3 ops/setup/fix_field_interpretation.py
  python3 ops/setup/fix_field_interpretation.py --apply
"""
import csv
import os
import re
import sys
import xmlrpc.client

URL  = 'http://localhost:8069'
DB   = 'rubicon'
USER = 'admin'
PASS = 'admin'

DRY_RUN = '--apply' not in sys.argv

BASE     = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CSV_PATH = os.path.join(BASE, "rubicon_addons/sis_party/data/sis.party.csv")

common = xmlrpc.client.ServerProxy(f'{URL}/xmlrpc/2/common')
uid    = common.authenticate(DB, USER, PASS, {})
assert uid, "Authentication failed!"
models = xmlrpc.client.ServerProxy(f'{URL}/xmlrpc/2/object')

def sr(model, domain, fields, limit=0):
    return models.execute_kw(DB, uid, PASS, model, 'search_read',
                             [domain], {'fields': fields, 'limit': limit})
def write(model, ids, vals):
    return models.execute_kw(DB, uid, PASS, model, 'write', [ids, vals])
def create(model, vals):
    return models.execute_kw(DB, uid, PASS, model, 'create', [vals])

# ── State code sets ───────────────────────────────────────────────────────
US_STATES = {
    'AL','AK','AZ','AR','CA','CO','CT','DE','FL','GA','HI','ID','IL','IN',
    'IA','KS','KY','LA','ME','MD','MA','MI','MN','MS','MO','MT','NE','NV',
    'NH','NJ','NM','NY','NC','ND','OH','OK','OR','PA','RI','SC','SD','TN',
    'TX','UT','VT','VA','WA','WV','WI','WY','DC',
}
AU_STATES = {'NSW','VIC','QLD','SA','WA','TAS','NT','ACT'}

PHONE_RE = re.compile(r'^[\+\d\s\-\(\)\.]{7,}$')

def looks_like_phone(val):
    if not val:
        return False
    digits = re.sub(r'\D', '', val)
    return len(digits) >= 7

def is_state_code(val):
    v = (val or '').strip().upper()
    return v in US_STATES or v in AU_STATES

# ── SIS country code → ISO ────────────────────────────────────────────────
SIS_TO_ISO = {
    'AE':'AE','AR':'AR','AU':'AU','BE':'BE','BT':'BL','BZ':'BR','CA':'CA',
    'CB':'CO','CH':'CL','CN':'CN','CO':'CR','EG':'EG','EN':'GB','FR':'FR',
    'GM':'DE','GR':'GR','HD':'HN','HK':'HK','HO':'NL','IN':'ID','IS':'IL',
    'IT':'IT','JP':'JP','KR':'KR','ME':'MX','ML':'MY','NC':'NC','NL':'NL',
    'NZ':'NZ','RU':'RU','SA':'ZA','SG':'SG','SP':'ES','SU':'SA','SW':'CH',
    'TA':'TZ','TH':'TH','TU':'TR','TW':'TW','UK':'UA','US':'US','VE':'VE',
}

print("Loading lookups...")
countries_raw = sr('res.country', [], ['id', 'code'])
country_by_iso = {c['code'].upper(): c['id'] for c in countries_raw}

states_raw = sr('res.country.state', [], ['id', 'code', 'country_id'])
# Build: (state_code, country_id) → state Odoo id
state_by_code_country = {}
for s in states_raw:
    key = (s['code'].upper(), s['country_id'][0] if s['country_id'] else 0)
    state_by_code_country[key] = s['id']
# Also by state code alone (for US default)
state_by_code_us = {}
us_id = country_by_iso.get('US')
for s in states_raw:
    if s['country_id'] and s['country_id'][0] == us_id:
        state_by_code_us[s['code'].upper()] = s['id']
au_id = country_by_iso.get('AU')
state_by_code_au = {}
for s in states_raw:
    if s['country_id'] and s['country_id'][0] == au_id:
        state_by_code_au[s['code'].upper()] = s['id']

print("Loading SIS partners...")
FIELDS = ['id','sis_code','name','city','state_id','country_id','website',
          'sis_ship_address','sis_ship_country_id','sis_phone_ids','bank_ids']
partners = sr('res.partner', [('sis_code','!=',False),('is_company','=',True)], FIELDS)
partner_by_code = {}
for p in partners:
    if p['sis_code'] and p['sis_code'] not in partner_by_code:
        partner_by_code[p['sis_code']] = p   # keep first (richest after dedup)
print(f"  {len(partner_by_code)} unique SIS codes")

# ── Read CSV ──────────────────────────────────────────────────────────────
print(f"Reading CSV: {CSV_PATH}")
rows = []
with open(CSV_PATH, newline='', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        rows.append(row)

# Build contact-row lookup: sis_party_N → contact row
contact_rows = {}
for row in rows:
    if row.get('contact_type') == 'individual':
        parent = row.get('parent_id/id', '').strip()
        if parent:
            contact_rows[parent] = row
# Build company XML id lookup: code → xml_id
code_to_xmlid = {}
for row in rows:
    if row.get('contact_type') == 'company':
        code_to_xmlid[row.get('code','').strip()] = row.get('id','').strip()

# ── Process ───────────────────────────────────────────────────────────────
fixed_website = 0
fixed_city    = 0
fixed_ship    = 0
fixed_bank    = 0
skipped       = 0

print(f"\n{'='*70}")
print(f"FIX 1 — website = phone number")
print(f"{'='*70}")

for p in partners:
    ws = (p.get('website') or '').strip()
    if not ws:
        continue
    # Remove "http://" prefix added by Odoo, check remaining
    raw = re.sub(r'^https?://', '', ws).strip()
    if looks_like_phone(raw) and not raw.startswith('www.') and '.' not in raw.split()[0]:
        print(f"  [{p['sis_code']:8}] {p['name'][:35]}  website={ws!r}")
        if not DRY_RUN:
            vals = {'website': False}
            # Add as second phone if not already there and phones not full
            existing_phones = sr('res.partner.phone', [('partner_id','=',p['id'])], ['phone'])
            already = [ep['phone'] for ep in existing_phones]
            if raw not in already:
                try:
                    create('res.partner.phone', {'partner_id': p['id'], 'name': 'Phone 2', 'phone': raw})
                except Exception:
                    pass  # field might not accept creation this way
            write('res.partner', [p['id']], vals)
        fixed_website += 1

print(f"\n→ {fixed_website} website fields to fix")

print(f"\n{'='*70}")
print(f"FIX 2 — city = state code")
print(f"{'='*70}")

for p in partners:
    city = (p.get('city') or '').strip()
    if not city or not is_state_code(city):
        continue
    city_up = city.upper()
    country_id = p['country_id'][0] if p['country_id'] else None

    state_id = None
    if city_up in US_STATES:
        state_id = state_by_code_us.get(city_up)
    elif city_up in AU_STATES:
        state_id = state_by_code_au.get(city_up)

    print(f"  [{p['sis_code']:8}] {p['name'][:35]}  city={city!r} → state_id={state_id}")
    if not DRY_RUN and state_id:
        write('res.partner', [p['id']], {'city': False, 'state_id': state_id})
    fixed_city += 1

print(f"\n→ {fixed_city} city fields to fix")

print(f"\n{'='*70}")
print(f"FIX 3 — Extract ship address + bank info from contact rows")
print(f"{'='*70}")
# Contact row column interpretation (based on observed pattern):
#   city       → ship street line (misaligned from original SIS ShipAdd2)
#   homepage   → ship state abbreviation
#   fax        → ship zip
#   email      → ship country code (2 letters) or ISO code
#   notes      → bank name
#   group_code → bank address line 1
#   ship_stamp → additional phone / contact notes

for code, p in partner_by_code.items():
    xml_id = code_to_xmlid.get(code)
    if not xml_id:
        continue
    contact = contact_rows.get(xml_id)
    if not contact:
        continue

    c_street = contact.get('city','').strip()        # misaligned ship street
    c_state  = contact.get('homepage','').strip()    # misaligned ship state
    c_zip    = contact.get('fax','').strip()         # misaligned ship zip
    c_ctry   = contact.get('email','').strip()       # misaligned ship country
    c_bank   = contact.get('notes','').strip()       # bank name
    c_badd   = contact.get('group_code','').strip()  # bank address

    vals = {}

    # Ship address — only if not already set
    if c_street and not p.get('sis_ship_address'):
        # Validate: looks like an actual street (contains digit or street keyword)
        if re.search(r'\d|st\.|ave|blvd|road|street|drive|lane|way|plaza|suite',
                     c_street, re.I):
            vals['sis_ship_address'] = c_street

    # Ship country
    if c_ctry and not p.get('sis_ship_country_id'):
        c_ctry_up = c_ctry.upper()
        iso = SIS_TO_ISO.get(c_ctry_up, c_ctry_up)
        cid = country_by_iso.get(iso)
        if cid:
            vals['sis_ship_country_id'] = cid

    if vals:
        detail = '  '.join(f"{k}={str(v)[:30]!r}" for k,v in vals.items())
        print(f"  [{code:8}] {p['name'][:30]}  {detail}")
        if not DRY_RUN:
            try:
                write('res.partner', [p['id']], vals)
                fixed_ship += 1
            except Exception as e:
                print(f"    ⚠ {e}")

    # Bank info — only if partner has no bank accounts yet
    if c_bank and not p.get('bank_ids'):
        bank_line = c_bank
        if c_badd:
            bank_line += f", {c_badd}"
        print(f"  [{code:8}] BANK: {bank_line[:60]}")
        # Note: creating res.partner.bank requires a valid bank; we store as comment instead
        if not DRY_RUN:
            existing_comment = (
                models.execute_kw(DB,uid,PASS,'res.partner','read',
                                  [[p['id']]],{'fields':['comment']})[0].get('comment') or ''
            )
            if c_bank not in (existing_comment or ''):
                new_comment = (existing_comment + f"\nBank: {bank_line}").strip()
                write('res.partner', [p['id']], {'comment': new_comment})
                fixed_bank += 1

print(f"\n→ {fixed_ship} ship addresses + {fixed_bank} bank notes to fix")

print(f"\n{'='*70}")
if DRY_RUN:
    print("⚠  DRY-RUN — no changes made. Pass --apply to execute.")
else:
    print(f"✅ Done!")
    print(f"   website fixed  : {fixed_website}")
    print(f"   city fixed     : {fixed_city}")
    print(f"   ship fixed     : {fixed_ship}")
    print(f"   bank noted     : {fixed_bank}")
print(f"{'='*70}")
