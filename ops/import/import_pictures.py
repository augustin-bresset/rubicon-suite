"""
Import photos and drawings into pdp.picture from data/pictures/.

Reads manifest.csv produced by ops/export/export_pictures_products.py.

Behaviour per manifest row type
---------------------------------
model          → create/update pdp.picture with scope='model'
                 and product_ids = all products belonging to that model (M2M)

model_drawing  → add drawing_1920 to the existing scope='model' picture for that model
                 (picture must have been imported first by a 'model' row)

product        → create pdp.picture with scope='product', product_ids=[<product>]
                 (product-specific photo from Snapshots; shown in preference to the
                  model thumbnail when displayed in the workspace)
                 Fallback: if the exact product code is not found but the model exists,
                 the photo is imported with scope='model' instead of being skipped.

Model code fallback
-------------------
Some Sketches.Model values lack the canonical zero-padding used in Odoo
(e.g. "CF1" instead of "CF001"). When a code is not found as-is, the
importer tries the zero-padded variant before giving up.

Run
---
  make import-pictures
  # or directly:
  docker compose exec -T odoo odoo shell -d rubicon --no-http < ops/import/import_pictures.py
"""
import base64
import binascii
import csv
import hashlib
import io
import os
import re
import traceback

# ── Guard ──────────────────────────────────────────────────────────────────
if "pdp.picture" not in env.registry.models:
    raise RuntimeError("Module pdp_picture not installed.")

Picture = env["pdp.picture"]
Model   = env["pdp.product.model"]
Product = env["pdp.product"]

BASE_PATH  = "/mnt/extra-addons/pictures"
MANIFEST   = os.path.join(BASE_PATH, "manifest.csv")
BATCH_SIZE = int(os.environ.get("PICTURE_IMPORT_BATCH", "25"))
CHUNK_SIZE = int(os.environ.get("PICTURE_IMPORT_CHUNK", str(3 * 1024 * 1024)))

if not os.path.isdir(BASE_PATH):
    raise RuntimeError(f"Directory not found: {BASE_PATH}")
if not os.path.isfile(MANIFEST):
    raise RuntimeError(f"manifest.csv not found in {BASE_PATH}. Run make export-pictures first.")


# ── Helpers ────────────────────────────────────────────────────────────────

def iter_base64(path, chunk_size):
    """Stream-encode a file to base64, returning (b64_bytes, md5_hex)."""
    digest = hashlib.md5()
    buf    = io.BytesIO()
    tail   = b""
    with open(path, "rb") as fh:
        while True:
            chunk = fh.read(chunk_size)
            if not chunk:
                break
            digest.update(chunk)
            chunk  = tail + chunk
            tail   = b""
            length = (len(chunk) // 3) * 3
            if length:
                buf.write(base64.b64encode(chunk[:length]))
                tail = chunk[length:]
            else:
                tail = chunk
        if tail:
            buf.write(base64.b64encode(tail))
    return buf.getvalue(), digest.hexdigest()


def commit(n):
    env.cr.commit()
    env.clear()
    print(f"  committed {n} records")


def zero_padded(code):
    """
    Return zero-padded variant of a model code, or None if not applicable.
    e.g. 'CF1' → 'CF001', 'CF3A' → 'CF003A', 'R132' → None (already 3 digits)
    """
    m = re.match(r'^([A-Z]+)(\d{1,2})([A-Z]?)$', code)
    if not m:
        return None
    prefix, num, suffix = m.groups()
    padded = prefix + num.zfill(3) + suffix
    return padded if padded != code else None


def find_model(code):
    """
    Look up a pdp.product.model by code, with zero-padding fallback.
    Returns the model record (possibly empty) and the code actually used.
    """
    model = Model.search([("code", "=", code)], limit=1)
    if model:
        return model, code
    alt = zero_padded(code)
    if alt:
        model = Model.search([("code", "=", alt)], limit=1)
        if model:
            return model, alt
    return Model.browse(), code


# ── Pre-load caches ────────────────────────────────────────────────────────

print("Loading model → products map …")
all_prods = Product.search([])
model_to_product_ids = {}
for p in all_prods:
    if p.model_id:
        model_to_product_ids.setdefault(p.model_id.id, []).append(p.id)
print(f"  {len(all_prods)} products across {len(model_to_product_ids)} models.\n")


# ── Read manifest ──────────────────────────────────────────────────────────

with open(MANIFEST, newline="") as f:
    rows = list(csv.DictReader(f))

# Process in order: model photos first, then drawings, then product photos
ORDER = {"model": 0, "model_drawing": 1, "product": 2}
rows.sort(key=lambda r: ORDER.get(r["type"], 9))

print(f"Processing {len(rows)} manifest entries …\n")

created = updated = linked = drawing_added = skipped = errors = 0
model_fallback = 0   # Snapshot photos rescued by falling back to model scope
batch_n = 0

for entry in rows:
    fname    = entry["filename"]
    row_type = entry["type"]
    code     = entry["code"].strip()
    full_path = os.path.join(BASE_PATH, fname)

    if not os.path.isfile(full_path):
        skipped += 1
        continue

    try:
        b64, chk = iter_base64(full_path, CHUNK_SIZE)
    except (OSError, MemoryError, binascii.Error) as exc:
        print(f"  {fname}: read error ({exc})")
        errors += 1
        continue

    try:
        with env.cr.savepoint():

            # ── Model photo ────────────────────────────────────────────────
            if row_type == "model":
                model, used_code = find_model(code)
                if not model:
                    skipped += 1
                    continue
                product_ids = model_to_product_ids.get(model.id, [])

                # Dedup by checksum
                existing = Picture.search([("checksum", "=", chk)], limit=1)
                if existing:
                    new_pids = [p for p in product_ids if p not in existing.product_ids.ids]
                    needs = {}
                    if new_pids:
                        needs["product_ids"] = [(4, pid) for pid in new_pids]
                    if existing.scope != "model":
                        needs["scope"] = "model"
                    if needs:
                        existing.write(needs)
                        linked += 1
                    else:
                        skipped += 1
                else:
                    # Find existing model picture by matching product links + scope
                    pic = Picture.search(
                        [("scope", "=", "model"), ("product_ids", "in", product_ids)],
                        limit=1
                    ) if product_ids else Picture.browse()
                    vals = {
                        "scope":       "model",
                        "filename":    fname,
                        "image":       b64,
                        "checksum":    chk,
                        "product_ids": [(6, 0, product_ids)],
                        "source_date": entry.get("source_date") or False,
                    }
                    if pic:
                        if pic.checksum != chk:
                            pic.write(vals)
                            updated += 1
                        else:
                            skipped += 1
                    else:
                        Picture.create(vals)
                        created += 1

            # ── Drawing ────────────────────────────────────────────────────
            elif row_type == "model_drawing":
                model, used_code = find_model(code)
                if not model:
                    skipped += 1
                    continue
                product_ids = model_to_product_ids.get(model.id, [])
                pic = Picture.search(
                    [("scope", "=", "model"), ("product_ids", "in", product_ids)],
                    limit=1
                ) if product_ids else Picture.browse()
                if pic and not pic.drawing_1920:
                    pic.write({"drawing_1920": b64, "drawing_filename": fname})
                    drawing_added += 1
                else:
                    skipped += 1

            # ── Product-specific photo (from Snapshots) ────────────────────
            elif row_type == "product":
                product = Product.search([("code", "=", code)], limit=1)

                if product:
                    # Exact product match → scope='product'
                    existing = Picture.search([("checksum", "=", chk)], limit=1)
                    if existing:
                        needs = {}
                        if product.id not in existing.product_ids.ids:
                            needs["product_ids"] = [(4, product.id)]
                        if existing.scope != "product":
                            needs["scope"] = "product"
                        if needs:
                            existing.write(needs)
                            linked += 1
                        else:
                            skipped += 1
                    else:
                        pic = Picture.search(
                            [("scope", "=", "product"), ("product_ids", "in", [product.id])],
                            limit=1
                        )
                        vals = {
                            "scope":       "product",
                            "filename":    fname,
                            "image":       b64,
                            "checksum":    chk,
                            "product_ids": [(6, 0, [product.id])],
                            "source_date": entry.get("source_date") or False,
                        }
                        if pic:
                            if pic.checksum != chk:
                                pic.write(vals)
                                updated += 1
                            else:
                                skipped += 1
                        else:
                            Picture.create(vals)
                            created += 1

                else:
                    # Product not found: try to attach to the model (scope='model')
                    # Product code format: {ModelCode}-{StoneComposition}/{Metal}
                    # Stone composition codes changed during Odoo import, so the
                    # Snapshot code won't match current product codes.
                    dash = code.find("-")
                    model_code = code[:dash] if dash >= 0 else ""
                    if not model_code:
                        skipped += 1
                        continue

                    model, used_code = find_model(model_code)
                    if not model:
                        skipped += 1
                        continue

                    product_ids = model_to_product_ids.get(model.id, [])
                    if not product_ids:
                        skipped += 1
                        continue

                    # Only attach if the model doesn't already have a picture
                    # (the Sketches photo is better quality; don't overwrite it)
                    existing_model_pic = Picture.search(
                        [("scope", "=", "model"), ("product_ids", "in", product_ids)],
                        limit=1
                    )
                    if existing_model_pic:
                        # Model already has a photo from Sketches — skip
                        skipped += 1
                        continue

                    existing = Picture.search([("checksum", "=", chk)], limit=1)
                    if existing:
                        new_pids = [p for p in product_ids if p not in existing.product_ids.ids]
                        if new_pids or existing.scope != "model":
                            needs = {"scope": "model"}
                            if new_pids:
                                needs["product_ids"] = [(4, pid) for pid in new_pids]
                            existing.write(needs)
                            linked += 1
                        else:
                            skipped += 1
                    else:
                        Picture.create({
                            "scope":       "model",
                            "filename":    fname,
                            "image":       b64,
                            "checksum":    chk,
                            "product_ids": [(6, 0, product_ids)],
                            "source_date": entry.get("source_date") or False,
                        })
                        created += 1
                        model_fallback += 1

    except Exception as exc:
        print(f"  {fname}: failed ({exc.__class__.__name__}: {exc})")
        traceback.print_exc()
        env.clear()
        errors += 1
        continue

    batch_n += 1
    if BATCH_SIZE and batch_n >= BATCH_SIZE:
        commit(batch_n)
        batch_n = 0

if batch_n:
    commit(batch_n)

print(
    f"\nDone."
    f"\n  created={created}, updated={updated}, linked={linked},"
    f"\n  drawings_added={drawing_added}, model_fallback={model_fallback},"
    f"\n  skipped={skipped}, errors={errors}"
)
