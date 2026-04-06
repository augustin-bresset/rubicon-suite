"""
Delete pdp.picture records that have no product links (orphans).

Context
-------
An older import run created pdp.picture records without linking them to any
product via the M2M. These records are invisible in the workspace (nothing
can resolve them) and waste filestore space.

Orphans = pdp.picture where product_ids is empty.

Run
---
  docker compose exec -T odoo odoo shell -d rubicon --no-http < ops/cleanup/cleanup_orphan_pictures.py
"""

Picture = env["pdp.picture"]

orphans = Picture.search([("product_ids", "=", False)])

print(f"Found {len(orphans)} orphan picture(s) (no product links).")

if not orphans:
    print("Nothing to do.")
else:
    by_scope = {}
    for p in orphans:
        by_scope[p.scope] = by_scope.get(p.scope, 0) + 1
    for scope, n in sorted(by_scope.items()):
        print(f"  scope='{scope}': {n}")

    orphans.unlink()
    env.cr.commit()
    print(f"\nDeleted {len(orphans)} orphan picture(s).")
    remaining = Picture.search_count([])
    print(f"Remaining pictures: {remaining}")
