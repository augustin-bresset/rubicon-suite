#!/usr/bin/env python3
"""
Extract data from sis.party.csv contact rows and patch res.partner records.

The contact rows in the CSV contain misaligned shipment + bank data:
  city       → ship address line (street)
  homepage   → ship state abbreviation
  fax        → ship zip
  email      → ship country code (2-letter SIS code)
  notes      → bank name
  group_code → bank address (first line)
  ship_stamp → Fed.Ex.Acc content (phone/fax)

Also patches:
  - sis_contact  from individual row 'company' (person's name)
  - sis_fax      from company row 'fax' column
  - sis_phone_ids Phone2 from company row 'homepage' (when it's a phone number)

DRY-RUN by default. Pass --apply to execute.

Run:
  python3 ops/setup/patch_contact_data.py
  python3 ops/setup/patch_contact_data.py --apply
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

SIS_TO_ISO = {
    'AE':'AE','AR':'AR','AU':'AU','BE':'BE','BT':'BL','BZ':'BR','CA':'CA',
    'CB':'CO','CH':'CL','CN':'CN','CO':'CR','EG':'EG','EN':'GB','FR':'FR',
    'GM':'DE','GR':'GR','HD':'HN','HK':'HK','HO':'NL','IN':'ID','IS':'IL',
    'IT':'IT','JP':'JP','KR':'KR','ME':'MX','ML':'MY','NC':'NC','NL':'NL',
    'NZ':'NZ','RU':'RU','SA':'ZA','SG':'SG','SP':'ES','SU':'SA','SW':'CH',
    'TA':'TZ','TH':'TH','TU':'TR','TW':'TW','UK':'UA','US':'US','VE':'VE',
}

PHONE_RE = re.compile(r'^[\+\d\s\-\(\)\.]{7,}$')

def looks_like_phone(val):
    if not val:
        return False
    digits = re.sub(r'\D', '', val)
    return len(digits) >= 7 and bool(PHONE_RE.match(val.strip()))

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

# Load partners
print("Loading SIS partners...")
partners = sr('res.partner', [('sis_code','!=',False),('is_company','=',True)],
              ['id','sis_code','name','sis_contact',
               'sis_ship_state','sis_ship_zip','sis_ship_country_id','sis_ship_fedex_acc',
               'bank_ids','sis_phone_ids'])
partner_by_code = {}
for p in partners:
    if p['sis_code'] and p['sis_code'] not in partner_by_code:
        partner_by_code[p['sis_code']] = p
print(f"  {len(partner_by_code)} unique SIS companies")

# Load country lookup
countries = sr('res.country', [], ['id','code'])
cid_by_iso = {c['code'].upper(): c['id'] for c in countries}

# Read CSV
rows = []
with open(CSV_PATH, newline='', encoding='utf-8') as f:
    for row in csv.DictReader(f):
        rows.append(row)

# Build lookup: xml_id → company row, xml_id → contact row
company_by_xmlid = {}
contact_by_xmlid = {}
for row in rows:
    xmlid = row.get('id','').strip()
    if row.get('contact_type') == 'company':
        company_by_xmlid[xmlid] = row
    elif row.get('contact_type') == 'individual':
        parent = row.get('parent_id/id','').strip()
        if parent:
            contact_by_xmlid[parent] = row

# Build code → xml_id
code_to_xmlid = {r.get('code','').strip(): r.get('id','').strip()
                 for r in rows if r.get('contact_type') == 'company'}

# ── Stats ──────────────────────────────────────────────────────────────────
c_contact = 0
c_fax     = 0
c_phone2  = 0
c_ship    = 0
c_bank    = 0

print(f"\n{'='*70}")
print(f"Patching from CSV company + contact rows")
print(f"{'='*70}")

for code, p in partner_by_code.items():
    xmlid   = code_to_xmlid.get(code)
    co_row  = company_by_xmlid.get(xmlid, {})
    ct_row  = contact_by_xmlid.get(xmlid, {})
    vals    = {}

    # ── sis_contact (contact person name from individual row) ──────────────
    if not p.get('sis_contact'):
        ct_name = ct_row.get('company','').strip()
        if ct_name and ct_name != '0':
            vals['sis_contact'] = ct_name
            c_contact += 1

    # ── Fax + Phone2 via sis_phone_ids (res.partner.phone) ───────────────
    # Load existing labels to avoid duplicates
    existing_labels = set()
    if p.get('sis_phone_ids'):
        phones = sr('res.partner.phone', [('partner_id','=',p['id'])], ['name','phone'])
        existing_labels = {(ph.get('name','') or '').lower() for ph in phones}

    fax_val = co_row.get('fax','').strip()
    if fax_val and looks_like_phone(fax_val) and 'fax' not in existing_labels:
        if not DRY_RUN:
            try:
                create('res.partner.phone', {
                    'partner_id': p['id'],
                    'name': 'Fax',
                    'phone': fax_val,
                })
                c_fax += 1
            except Exception as e:
                print(f"  ⚠ [{code}] fax: {e}")
        else:
            c_fax += 1

    homepage = co_row.get('homepage','').strip()
    # homepage already handled earlier (website fix script cleared http:// versions)
    # Add as Phone 2 if it looks like a phone and not already in sis_phone_ids
    if homepage and looks_like_phone(homepage) and 'phone 2' not in existing_labels:
        if not DRY_RUN:
            try:
                create('res.partner.phone', {
                    'partner_id': p['id'],
                    'name': 'Phone 2',
                    'phone': homepage,
                })
                c_phone2 += 1
            except Exception as e:
                print(f"  ⚠ [{code}] phone2: {e}")
        else:
            c_phone2 += 1

    # ── Shipment fields from contact row ──────────────────────────────────
    # homepage col = ship state, fax col = ship zip, email col = ship country
    ct_state  = ct_row.get('homepage','').strip()
    ct_zip    = ct_row.get('fax','').strip()
    ct_ctry   = ct_row.get('email','').strip().upper()
    ct_fedex  = ct_row.get('ship_stamp','').strip()

    if ct_state and not p.get('sis_ship_state'):
        # Only use if looks like a state code (2 uppercase letters)
        if len(ct_state) <= 10 and ct_state.replace(' ','').isalpha():
            vals['sis_ship_state'] = ct_state

    if ct_zip and not p.get('sis_ship_zip'):
        # Only use if looks like a zip code (digits, or short alphanumeric)
        if re.match(r'^[\d]{3,10}$', ct_zip.strip()):
            vals['sis_ship_zip'] = ct_zip

    if ct_ctry and not p.get('sis_ship_country_id'):
        iso = SIS_TO_ISO.get(ct_ctry, ct_ctry)
        cid = cid_by_iso.get(iso)
        if cid:
            vals['sis_ship_country_id'] = cid

    # Fed.Ex.Acc — contact row ship_stamp contains phone/fax info
    if ct_fedex and not p.get('sis_ship_fedex_acc'):
        # Only if it looks like contact/phone info, not a general note
        if re.search(r'TEL|FAX|PHONE|\+\d|\d{7,}', ct_fedex, re.I):
            vals['sis_ship_fedex_acc'] = ct_fedex

    if any(k in vals for k in ['sis_ship_state','sis_ship_zip','sis_ship_country_id','sis_ship_fedex_acc']):
        c_ship += 1

    # ── Bank info from contact row → res.partner.bank ─────────────────────
    ct_bank_name = ct_row.get('notes','').strip()
    ct_bank_add  = ct_row.get('group_code','').strip()

    if ct_bank_name and not p.get('bank_ids'):
        print(f"  [{code:8}] BANK: {ct_bank_name[:40]}  addr={ct_bank_add[:30]!r}")
        if not DRY_RUN:
            try:
                create('res.partner.bank', {
                    'partner_id': p['id'],
                    'sis_bank_name': ct_bank_name,
                    'sis_bank_address': ct_bank_add or False,
                    'acc_number': 'unknown',   # required field on res.partner.bank
                })
                c_bank += 1
            except Exception as e:
                print(f"  ⚠ [{code}] bank: {e}")
        else:
            c_bank += 1

    # ── Apply ─────────────────────────────────────────────────────────────
    if vals:
        summary = ', '.join(f"{k}={str(v)[:20]!r}" for k,v in list(vals.items())[:4])
        print(f"  [{code:8}] {p['name'][:30]:30}  {summary}")
        if not DRY_RUN:
            try:
                write('res.partner', [p['id']], vals)
            except Exception as e:
                print(f"    ⚠ write error: {e}")

print(f"\n{'='*70}")
if DRY_RUN:
    print("⚠  DRY-RUN — no changes made. Pass --apply to execute.")
else:
    print("✅ Done!")
print(f"  sis_contact set  : {c_contact}")
print(f"  sis_fax set      : {c_fax}")
print(f"  Phone2 added     : {c_phone2}")
print(f"  Ship fields set  : {c_ship}")
print(f"  Bank name set    : {c_bank}")
print(f"{'='*70}")
