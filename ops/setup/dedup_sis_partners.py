#!/usr/bin/env python3
"""
Deduplicate res.partner records that share the same sis_code.

For each sis_code with N > 1 records, keeps the "richest" one (most non-empty
fields) and unlinks / deletes the others.

DRY-RUN by default. Pass --apply to actually delete.

Run:
  python3 ops/setup/dedup_sis_partners.py           # dry-run
  python3 ops/setup/dedup_sis_partners.py --apply   # real run
"""
import sys
import xmlrpc.client
from collections import defaultdict

URL  = 'http://localhost:8069'
DB   = 'rubicon'
USER = 'admin'
PASS = 'admin'

DRY_RUN = '--apply' not in sys.argv

common = xmlrpc.client.ServerProxy(f'{URL}/xmlrpc/2/common')
uid    = common.authenticate(DB, USER, PASS, {})
assert uid, "Authentication failed!"
models = xmlrpc.client.ServerProxy(f'{URL}/xmlrpc/2/object')

def sr(model, domain, fields, limit=0):
    return models.execute_kw(DB, uid, PASS, model, 'search_read',
                             [domain], {'fields': fields, 'limit': limit})

def unlink(model, ids):
    return models.execute_kw(DB, uid, PASS, model, 'unlink', [ids])

# --- Load all SIS partners (companies only) ---
FIELDS = [
    'id', 'name', 'sis_code',
    'street', 'street2', 'city', 'state_id', 'zip', 'country_id',
    'phone', 'email', 'website', 'comment',
    'sis_pay_term_id', 'sis_ship_method_id', 'sis_ship_stamp',
    'sis_group', 'sis_account',
    'bank_ids', 'sis_phone_ids',
]
partners = sr('res.partner', [('sis_code', '!=', False), ('is_company', '=', True)], FIELDS)
print(f"Loaded {len(partners)} SIS company records")

# --- Group by sis_code ---
by_code = defaultdict(list)
for p in partners:
    by_code[p['sis_code']].append(p)

dupes = {code: recs for code, recs in by_code.items() if len(recs) > 1}
print(f"Found {len(dupes)} sis_codes with duplicates "
      f"({sum(len(r) for r in dupes.values())} total records)")

if not dupes:
    print("Nothing to do.")
    sys.exit(0)

def richness(p):
    """Count non-empty meaningful fields — higher = richer record."""
    score = 0
    for field in ['street', 'street2', 'city', 'zip', 'phone', 'email',
                  'website', 'comment', 'sis_pay_term_id', 'sis_ship_method_id',
                  'sis_ship_stamp', 'sis_group', 'sis_account']:
        v = p.get(field)
        if v and v not in (False, '', []):
            score += 1
    if p.get('country_id'):
        score += 2           # country is very important
    if p.get('state_id'):
        score += 1
    score += len(p.get('bank_ids', []))
    score += len(p.get('sis_phone_ids', []))
    return score

to_delete = []
kept_ids  = []

print(f"\n{'CODE':<10} {'KEEP id':>8} {'DEL ids':>20}  RICHNESS")
print("-" * 60)

for code, recs in sorted(dupes.items()):
    scored = sorted(recs, key=richness, reverse=True)
    keep   = scored[0]
    delete = scored[1:]

    kept_ids.append(keep['id'])
    del_ids = [r['id'] for r in delete]
    to_delete.extend(del_ids)

    scores = [richness(r) for r in scored]
    print(f"  [{code:<8}] keep={keep['id']:>6}  del={str(del_ids):<20}  "
          f"scores={scores}")

print(f"\nWill keep   : {len(kept_ids)} records")
print(f"Will DELETE : {len(to_delete)} records")

if DRY_RUN:
    print("\n⚠  DRY-RUN — no changes made. Pass --apply to execute.")
    sys.exit(0)

# --- Confirm ---
print("\n⚠  This will PERMANENTLY DELETE records from the database.")
ans = input("Type 'yes' to proceed: ").strip().lower()
if ans != 'yes':
    print("Aborted.")
    sys.exit(0)

# --- Re-parent children of records being deleted ---
print("\nRe-parenting individuals linked to duplicate records...")
re_parented = 0
for code, recs in dupes.items():
    scored  = sorted(recs, key=richness, reverse=True)
    keep    = scored[0]
    del_recs = scored[1:]
    for dr in del_recs:
        children = sr('res.partner', [('parent_id', '=', dr['id'])], ['id', 'name'])
        if children:
            child_ids = [c['id'] for c in children]
            models.execute_kw(DB, uid, PASS, 'res.partner', 'write',
                              [child_ids, {'parent_id': keep['id']}])
            re_parented += len(children)
            print(f"  [{code}] re-parented {len(children)} child(ren) from id={dr['id']} → id={keep['id']}")

print(f"Re-parented {re_parented} individuals total")

# --- Delete in batches ---
print(f"\nDeleting {len(to_delete)} duplicate records...")
BATCH = 50
deleted = 0
errors  = 0
for i in range(0, len(to_delete), BATCH):
    batch = to_delete[i:i+BATCH]
    try:
        unlink('res.partner', batch)
        deleted += len(batch)
    except Exception as e:
        print(f"  ⚠ Batch {i//BATCH + 1} error: {e}")
        # Try one by one
        for rid in batch:
            try:
                unlink('res.partner', [rid])
                deleted += 1
            except Exception as e2:
                print(f"    ⚠ id={rid}: {e2}")
                errors += 1

print(f"\n✅ Done!")
print(f"   Deleted : {deleted}")
print(f"   Errors  : {errors}")

# --- Summary ---
remaining = sr('res.partner', [('sis_code', '!=', False), ('is_company', '=', True)], ['id'])
print(f"   SIS companies remaining: {len(remaining)}")
