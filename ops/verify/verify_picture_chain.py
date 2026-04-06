"""
Verify the complete picture chain for products and models.

For each product or model code, this script determines:
  · Which model it belongs to (code + drawing reference)
  · Whether a picture exists and at which level:
      - 'model'   → photo from Sketches, shared by all products of the model
                    identified by CatID+OrnID → model code (e.g. R132)
      - 'product' → photo from Snapshots, specific to one product variant
                    identified by CatID+OrnID+StoneID+GoldID (e.g. R132-GA+RHO/W)
  · Whether a drawing (technical sketch) exists

The distinction matters because:
  - A 'model' picture shows the base design, visible for all variants.
  - A 'product' picture shows a specific stone/metal combination.

Test case (confirmed):
  Product R132-GA+RHO+CT+PF+T/W → model R132 → drawing# RP128B
  Expected: model-scope picture present (from Sketches, key = "R132")

Usage
-----
Edit TEST_CODES below and run:
  docker compose exec -T odoo odoo shell -d rubicon --no-http < ops/verify/verify_picture_chain.py
"""

# ── Configure test subjects ────────────────────────────────────────────────

# Product codes to verify individually
TEST_PRODUCT_CODES = [
    "R132-GA+RHO+CT+PF+T/W",   # reference test case
]

# Model codes to verify individually
TEST_MODEL_CODES = [
    "R132",
]

# Drawing references to verify
TEST_DRAWING_REFS = [
    "RP128B",
]

# Set to True for a full coverage report across all models/products
RUN_FULL_REPORT = True


# ── Helpers ────────────────────────────────────────────────────────────────

Picture = env["pdp.picture"]
Model   = env["pdp.product.model"]
Product = env["pdp.product"]


def resolve_picture_for_product(product):
    """
    Return the best picture for a product and its resolution level.

    Resolution priority:
      1. scope='product' picture linked directly to this product
         (from Snapshots: CatID+OrnID+StoneID+GoldID)
      2. scope='model'   picture linked to any product of the same model
         (from Sketches:  CatID+OrnID → model code)

    Returns: (picture_record, level) where level is 'product', 'model', or None.
    """
    # Level 1: product-specific
    pic = Picture.search([
        ("scope", "=", "product"),
        ("product_ids", "in", [product.id]),
    ], limit=1)
    if pic:
        return pic, "product"

    # Level 2: model-scope
    if product.model_id:
        sibling_ids = Product.search([("model_id", "=", product.model_id.id)]).ids
        pic = Picture.search([
            ("scope", "=", "model"),
            ("product_ids", "in", sibling_ids),
        ], limit=1)
        if pic:
            return pic, "model"

    return Picture.browse(), None


def resolve_picture_for_model(model_rec):
    """
    Return the picture for a model and whether a drawing exists.
    """
    sibling_ids = Product.search([("model_id", "=", model_rec.id)]).ids
    if not sibling_ids:
        return Picture.browse(), None

    pic = Picture.search([
        ("scope", "=", "model"),
        ("product_ids", "in", sibling_ids),
    ], limit=1)
    level = "model" if pic else None
    return pic, level


def fmt_pic(pic, level):
    if not pic:
        return "NO PICTURE"
    has_drawing = bool(pic.drawing_filename)
    return (
        f"[{level.upper()}] file={pic.filename or '?'}  "
        f"drawing={'YES (' + pic.drawing_filename + ')' if has_drawing else 'no'}  "
        f"products={len(pic.product_ids)}"
    )


def sep(char="─", width=72):
    print(char * width)


# ── Individual tests ───────────────────────────────────────────────────────

sep("═")
print("  PICTURE CHAIN VERIFICATION")
sep("═")

for code in TEST_PRODUCT_CODES:
    sep()
    product = Product.search([("code", "=", code)], limit=1)
    if not product:
        print(f"PRODUCT {code!r}  → NOT FOUND IN ODOO")
        continue
    model_rec = product.model_id
    drawing   = model_rec.drawing if model_rec else None
    pic, level = resolve_picture_for_product(product)

    print(f"PRODUCT  : {code}")
    print(f"MODEL    : {model_rec.code if model_rec else '?'}  drawing#={drawing or 'none'}")
    print(f"PICTURE  : {fmt_pic(pic, level)}")

for code in TEST_MODEL_CODES:
    sep()
    model_rec = Model.search([("code", "=", code)], limit=1)
    if not model_rec:
        print(f"MODEL {code!r}  → NOT FOUND IN ODOO")
        continue
    pic, level = resolve_picture_for_model(model_rec)
    n_products = Product.search_count([("model_id", "=", model_rec.id)])

    print(f"MODEL    : {code}  drawing#={model_rec.drawing or 'none'}  products={n_products}")
    print(f"PICTURE  : {fmt_pic(pic, level)}")

for drawing_ref in TEST_DRAWING_REFS:
    sep()
    model_rec = Model.search([("drawing", "=", drawing_ref)], limit=1)
    if not model_rec:
        print(f"DRAWING# {drawing_ref!r}  → no model found in Odoo")
        continue
    pic, level = resolve_picture_for_model(model_rec)
    print(f"DRAWING# : {drawing_ref}  → model={model_rec.code}  products={Product.search_count([('model_id','=',model_rec.id)])}")
    print(f"PICTURE  : {fmt_pic(pic, level)}")


# ── Full coverage report ───────────────────────────────────────────────────

if RUN_FULL_REPORT:
    sep("═")
    print("  FULL COVERAGE REPORT")
    sep("═")

    all_models = Model.search([])
    all_products = Product.search([])

    total_models   = len(all_models)
    total_products = len(all_products)

    # Pre-build model → product list
    model_to_prods = {}
    for p in all_products:
        if p.model_id:
            model_to_prods.setdefault(p.model_id.id, []).append(p.id)

    # All pictures indexed by product_id
    all_pics = Picture.search([])
    model_scope_by_pid  = {}   # product_id → picture (model-scope)
    product_scope_by_pid = {}  # product_id → picture (product-scope)
    has_drawing_by_pid  = {}   # product_id → True if linked model pic has drawing

    for pic in all_pics:
        for pid in pic.product_ids.ids:
            if pic.scope == "model":
                model_scope_by_pid[pid] = pic
                if pic.drawing_filename:
                    has_drawing_by_pid[pid] = True
            elif pic.scope == "product":
                product_scope_by_pid[pid] = pic

    # Count models with pictures
    models_with_pic = 0
    models_with_drawing = 0
    for m in all_models:
        pids = model_to_prods.get(m.id, [])
        has_pic  = any(pid in model_scope_by_pid for pid in pids)
        has_draw = any(has_drawing_by_pid.get(pid) for pid in pids)
        if has_pic:
            models_with_pic += 1
        if has_draw:
            models_with_drawing += 1

    # Count products with pictures (any level)
    prods_with_model_pic   = sum(1 for p in all_products if p.id in model_scope_by_pid)
    prods_with_product_pic = sum(1 for p in all_products if p.id in product_scope_by_pid)
    prods_with_any_pic     = sum(
        1 for p in all_products
        if p.id in model_scope_by_pid or p.id in product_scope_by_pid
    )

    def pct(n, total):
        return f"{n}/{total} ({100*n//total if total else 0}%)"

    print(f"Models with scope='model' picture : {pct(models_with_pic, total_models)}")
    print(f"Models with drawing               : {pct(models_with_drawing, total_models)}")
    print()
    print(f"Products with model-scope picture  : {pct(prods_with_model_pic, total_products)}")
    print(f"Products with product-scope picture: {pct(prods_with_product_pic, total_products)}")
    print(f"Products with ANY picture          : {pct(prods_with_any_pic, total_products)}")
    print()

    # Sample models WITHOUT pictures
    no_pic_models = [
        m for m in all_models
        if not any(pid in model_scope_by_pid for pid in model_to_prods.get(m.id, []))
    ]
    print(f"Models without picture: {len(no_pic_models)}")
    if no_pic_models:
        sample = no_pic_models[:10]
        print(f"  Sample: {[m.code for m in sample]}")

    sep("═")
    print("Done.")
