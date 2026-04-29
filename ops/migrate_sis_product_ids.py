"""
Migration: populate sis.document.item.product_id from pdp.product via design code match.

This script is READ-ONLY regarding prices — it only sets the product_id FK.
No unit_price, amount, cost, or profit fields are touched.

Run via shell exec:
  docker compose exec odoo odoo shell -d rubicon < ops/migrate_sis_product_ids.py

Or dry-run (set DRY_RUN = True) to see counts without writing.
"""

DRY_RUN = False

env = env  # noqa: injected by odoo shell

# Load all pdp products: code → id
all_products = env['pdp.product'].sudo().search([])
code_to_id = {p.code: p.id for p in all_products if p.code}

print(f"PDP products loaded: {len(code_to_id)}")

# Find SIS items without product_id
unlinked = env['sis.document.item'].sudo().search([
    ('product_id', '=', False),
    ('design', '!=', False),
])
print(f"SIS items without product_id: {len(unlinked)}")

matched = []
for item in unlinked:
    pid = code_to_id.get(item.design)
    if pid:
        matched.append((item, pid))

print(f"Matchable by design code: {len(matched)} / {len(unlinked)}")

if not DRY_RUN and matched:
    for item, pid in matched:
        item.sudo().write({'product_id': pid})
    env.cr.commit()
    print("Done. product_id populated.")
elif DRY_RUN:
    print("DRY_RUN — no changes written.")
    # Show a sample
    for item, pid in matched[:10]:
        prod = env['pdp.product'].browse(pid)
        print(f"  item {item.id}: design={item.design!r} → product {pid} ({prod.code})")
