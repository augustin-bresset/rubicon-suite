#!/usr/bin/env python3
"""
Audit res.partner records that carry a sis_code (i.e. SIS parties).

Run:
  python3 ops/verify/verify_sis_partners.py
"""
import xmlrpc.client

URL = 'http://localhost:8069'
DB  = 'rubicon'
USER = 'admin'
PASS = 'admin'

common = xmlrpc.client.ServerProxy(f'{URL}/xmlrpc/2/common')
uid    = common.authenticate(DB, USER, PASS, {})
assert uid, "Authentication failed!"
models = xmlrpc.client.ServerProxy(f'{URL}/xmlrpc/2/object')

def sr(model, domain, fields, limit=0):
    return models.execute_kw(DB, uid, PASS, model, 'search_read',
                             [domain], {'fields': fields, 'limit': limit})

print("=" * 70)
print("SIS PARTNER VERIFICATION REPORT  (res.partner with sis_code)")
print("=" * 70)

BASE_DOM = [('sis_code', '!=', False)]
CO_DOM   = BASE_DOM + [('is_company', '=', True)]
IND_DOM  = BASE_DOM + [('is_company', '=', False)]

# ── Counts ────────────────────────────────────────────────────────────────
all_p  = sr('res.partner', BASE_DOM, ['id'])
cos    = sr('res.partner', CO_DOM,   ['id'])
inds   = sr('res.partner', IND_DOM,  ['id'])
print(f"\n📊 COUNTS")
print(f"   Total SIS partners : {len(all_p)}")
print(f"   Companies          : {len(cos)}")
print(f"   Individuals        : {len(inds)}")

# ── Parent linking ────────────────────────────────────────────────────────
orphans = sr('res.partner', IND_DOM + [('parent_id', '=', False)], ['id', 'name'])
print(f"\n🔗 PARENT-CHILD LINKING")
print(f"   Individuals without parent : {len(orphans)}")
for o in orphans[:5]:
    print(f"     ⚠  {o['name']}")
if len(orphans) > 5:
    print(f"     … and {len(orphans) - 5} more")

# ── Country ───────────────────────────────────────────────────────────────
no_country   = sr('res.partner', CO_DOM + [('country_id', '=', False)], ['id', 'sis_code', 'name'])
with_country = sr('res.partner', CO_DOM + [('country_id', '!=', False)], ['id'])
print(f"\n🌍 COUNTRY")
print(f"   With country    : {len(with_country)}")
print(f"   Without country : {len(no_country)}")
for n in no_country[:10]:
    print(f"     ⚠  [{n['sis_code']}] {n['name']}")
if len(no_country) > 10:
    print(f"     … and {len(no_country) - 10} more")

# ── Pay term ──────────────────────────────────────────────────────────────
no_pt   = sr('res.partner', CO_DOM + [('sis_pay_term_id', '=', False)], ['id'])
with_pt = sr('res.partner', CO_DOM + [('sis_pay_term_id', '!=', False)], ['id'])
print(f"\n💳 SIS PAY TERM")
print(f"   With pay term    : {len(with_pt)}")
print(f"   Without pay term : {len(no_pt)}")

# ── Shipper ───────────────────────────────────────────────────────────────
no_sh   = sr('res.partner', CO_DOM + [('sis_ship_method_id', '=', False)], ['id'])
with_sh = sr('res.partner', CO_DOM + [('sis_ship_method_id', '!=', False)], ['id'])
print(f"\n🚚 SIS SHIP METHOD")
print(f"   With shipper    : {len(with_sh)}")
print(f"   Without shipper : {len(no_sh)}")

# ── Customer / Vendor flags ───────────────────────────────────────────────
is_cust  = sr('res.partner', CO_DOM + [('sis_is_customer', '=', True)],  ['id'])
is_vend  = sr('res.partner', CO_DOM + [('sis_is_vendor',   '=', True)],  ['id'])
print(f"\n🏷  CUSTOMER / VENDOR FLAGS")
print(f"   sis_is_customer = True : {len(is_cust)}")
print(f"   sis_is_vendor   = True : {len(is_vend)}")

# ── Address completeness ──────────────────────────────────────────────────
no_street = sr('res.partner', CO_DOM + [('street', '=', False)], ['id'])
no_city   = sr('res.partner', CO_DOM + [('city',   '=', False)], ['id'])
print(f"\n📍 ADDRESS COMPLETENESS")
print(f"   Missing street : {len(no_street)}")
print(f"   Missing city   : {len(no_city)}")

# ── Communication ─────────────────────────────────────────────────────────
with_email = sr('res.partner', CO_DOM + [('email', '!=', False)], ['id'])
with_phone = sr('res.partner', CO_DOM + [('phone', '!=', False)], ['id'])
print(f"\n📞 COMMUNICATION")
print(f"   With email : {len(with_email)}")
print(f"   With phone : {len(with_phone)}")

# ── Sample companies ──────────────────────────────────────────────────────
print(f"\n👥 SAMPLE COMPANIES (first 10)")
samples = sr('res.partner', CO_DOM,
             ['sis_code', 'name', 'country_id', 'sis_pay_term_id',
              'sis_ship_method_id', 'sis_is_customer', 'sis_is_vendor'], limit=10)
for s in samples:
    country  = s['country_id'][1]         if s['country_id']         else '—'
    pay_term = s['sis_pay_term_id'][1]    if s['sis_pay_term_id']    else '—'
    shipper  = s['sis_ship_method_id'][1] if s['sis_ship_method_id'] else '—'
    flags    = ('C' if s['sis_is_customer'] else '-') + ('V' if s['sis_is_vendor'] else '-')
    print(f"   [{s['sis_code']:6}] {s['name'][:35]:35}  {country:22}  pay={pay_term:12}  ship={shipper:12}  [{flags}]")

print(f"\n{'=' * 70}")
print("[SUCCESS] Done!")
print(f"{'=' * 70}")
