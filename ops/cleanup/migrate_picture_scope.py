"""
Migrate pdp.picture records to the new `scope` field.

Context
-------
Pictures imported before the `scope` field was added all have scope='product'
(ORM default).  Model-level thumbnails were imported with product_ids pointing
to ALL products of the model, while product-specific photos point to exactly
one product.

Heuristic
---------
  len(product_ids) > 1  → scope='model'   (definitely a model thumbnail)
  len(product_ids) == 1 → scope='product' (product-specific, or single-product
                           model where the distinction is irrelevant)
  len(product_ids) == 0 → orphan, left untouched

Run
---
  make migrate-picture-scope
  # or directly:
  docker compose exec -T odoo odoo shell -d rubicon --no-http < ops/cleanup/migrate_picture_scope.py
"""

Picture = env["pdp.picture"]

total     = Picture.search_count([])
to_fix    = Picture.search([("scope", "=", "product"), ("product_ids", "!=", False)])

print(f"Total pictures          : {total}")
print(f"Candidates to inspect   : {len(to_fix)}")

updated = 0
for pic in to_fix:
    if len(pic.product_ids) > 1:
        pic.scope = "model"
        updated += 1

env.cr.commit()

after_model   = Picture.search_count([("scope", "=", "model")])
after_product = Picture.search_count([("scope", "=", "product")])

print(f"\nDone.")
print(f"  scope='model'   : {after_model}")
print(f"  scope='product' : {after_product}")
print(f"  updated         : {updated}")
