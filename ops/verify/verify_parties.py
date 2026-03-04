#!/usr/bin/env python3
"""Verify sis.party data in Odoo via XML-RPC."""
import xmlrpc.client

URL = 'http://localhost:8069'
DB = 'rubicon'
USER = 'admin'
PASS = 'admin'

# --- Connect ---
common = xmlrpc.client.ServerProxy(f'{URL}/xmlrpc/2/common')
uid = common.authenticate(DB, USER, PASS, {})
assert uid, "Authentication failed!"
models = xmlrpc.client.ServerProxy(f'{URL}/xmlrpc/2/object')

def search_read(model, domain, fields, limit=0):
    return models.execute_kw(DB, uid, PASS, model, 'search_read',
                             [domain], {'fields': fields, 'limit': limit})

# =========================================================================
print("=" * 70)
print("SIS PARTY VERIFICATION REPORT")
print("=" * 70)

# 1. Total counts
all_parties = search_read('sis.party', [], ['id'])
companies = search_read('sis.party', [('contact_type', '=', 'company')], ['id'])
individuals = search_read('sis.party', [('contact_type', '=', 'individual')], ['id'])
print(f"\n📊 COUNTS")
print(f"   Total parties:  {len(all_parties)}")
print(f"   Companies:      {len(companies)}")
print(f"   Individuals:    {len(individuals)}")

# 2. Parent-child linking
linked = search_read('sis.party', [('parent_id', '!=', False)], ['id', 'company', 'parent_id'])
orphans = search_read('sis.party', [('contact_type', '=', 'individual'), ('parent_id', '=', False)], ['id', 'company'])
print(f"\n🔗 PARENT-CHILD LINKING")
print(f"   Individuals with parent:    {len(linked)}")
print(f"   Individuals WITHOUT parent: {len(orphans)}")
if orphans:
    for o in orphans[:5]:
        print(f"     ⚠ [{o['id']}] {o['company']}")
    if len(orphans) > 5:
        print(f"     ... and {len(orphans) - 5} more")

# 3. Sample company with contacts
sample_companies = search_read('sis.party', [('contact_type', '=', 'company'), ('child_ids', '!=', False)],
                                ['id', 'company', 'code', 'country_id', 'child_ids'], limit=5)
print(f"\n👥 SAMPLE COMPANIES WITH CONTACTS (first 5)")
for c in sample_companies:
    country = c['country_id'][1] if c['country_id'] else 'N/A'
    contacts = search_read('sis.party', [('id', 'in', c['child_ids'])], ['company', 'phone', 'email'])
    contact_names = [ct['company'] for ct in contacts]
    print(f"   [{c['code']}] {c['company']} ({country})")
    for ct in contacts:
        print(f"     └ {ct['company']}  📞 {ct.get('phone') or '-'}  ✉ {ct.get('email') or '-'}")

# 4. Country resolution check
no_country = search_read('sis.party', [('contact_type', '=', 'company'), ('country_id', '=', False)],
                         ['id', 'company', 'code'], limit=10)
with_country = search_read('sis.party', [('contact_type', '=', 'company'), ('country_id', '!=', False)],
                           ['id'])
print(f"\n🌍 COUNTRY RESOLUTION")
print(f"   Companies with country:    {len(with_country)}")
print(f"   Companies without country: {len(no_country)}")
if no_country:
    for n in no_country[:5]:
        print(f"     ⚠ [{n['code']}] {n['company']}")

# 5. Field quality checks
print(f"\n📋 FIELD QUALITY")
# Check emails
bad_emails = search_read('sis.party', [('email', 'like', 'mailto:')], ['id', 'company', 'email'])
print(f"   Emails with 'mailto:' prefix: {len(bad_emails)}")

# Check phones (very basic)
with_phone = search_read('sis.party', [('contact_type', '=', 'company'), ('phone', '!=', False)], ['id'])
print(f"   Companies with phone: {len(with_phone)}")

with_email = search_read('sis.party', [('contact_type', '=', 'company'), ('email', '!=', False)], ['id'])
print(f"   Companies with email: {len(with_email)}")

# 6. Check for broken IDs (should be 0)
broken = search_read('sis.party', [('code', '=', '0'), ('contact_type', '=', 'company')], ['id', 'company'])
print(f"\n🔧 DATA INTEGRITY")
print(f"   Companies with code='0': {len(broken)}")

print(f"\n{'=' * 70}")
print("✅ Verification complete!")
print(f"{'=' * 70}")
