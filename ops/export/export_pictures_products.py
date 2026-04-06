"""
Export photos and drawings from Pictures.bak into data/pictures/.

Sources
-------
PICTURES.dbo.Sketches  (~10 656 rows)
  Keyed by CatID + OrnID.  The Model column = constructed model code
  (e.g. CatID="R", OrnID="132" → Model="R132"), which matches
  pdp.product.model.code in Odoo.
  · Picture → data/pictures/{Model}.jpg          type=model
  · Sketch  → data/pictures/{Model}_drawing.jpg  type=model_drawing

  Note: Sketches.Model is always the model code (e.g. R132), never the
  design drawing reference (e.g. RP128B). The drawing reference is a
  separate field (pdp.product.model.drawing in Odoo), populated from
  Models.csv during the initial data import.

  Fallback: if Model is NULL or empty, the code is reconstructed from
  RTRIM(CatID) + RTRIM(OrnID) zero-padded to 3 digits.

PICTURES.dbo.Snapshots (~250 rows)
  Keyed by CatID + OrnID + StoneID + GoldID → product-specific photo.
  · Picture → data/pictures/{product_code_safe}.jpg  type=product
    where product_code = RTRIM(CatID)+RTRIM(OrnID)+'-'+StoneID+'/'+GoldID
    and   product_code_safe replaces '/' with '~'  (e.g. B001-EMCS+CITA~W.jpg)

PICTURES.dbo.TSketches (same schema as Sketches, 2 rows only)
  Contains high-resolution replacements for 2 models already present in
  Sketches (E1514C ×4.7 larger, P761 ×15 larger).
  These rows are exported FIRST and override the Sketches photo for those
  2 models during import (same filename prefix, higher quality).

A manifest.csv is written alongside the images with columns:
  filename, type, code, cat_id, orn_id, source_date
  · cat_id / orn_id preserve the raw old-DB keys for traceability.
  · source_date is the LastUpdated timestamp from the source row (ISO format).
  · For product rows, cat_id+orn_id give the model code; stone+gold are
    embedded in the product code itself.

Example:
  R132.jpg, model, R132, R, 132, 2008-07-31 16:16:27
  R132_drawing.jpg, model_drawing, R132, R, 132, 2008-07-31 16:16:27
  R132-GA+RHO~W.jpg, product, R132-GA+RHO/W, R, 132, 2002-03-13 17:36:28

Prerequisites
-------------
SQL Server container 'sqlsrv' running with Pictures.bak restored.
See meta/doc/backup.md for full setup instructions.

Run
---
  python3 ops/export/export_pictures_products.py
or
  make export-pictures
"""
import csv
import os
import re
import sys

try:
    import pyodbc
    from tqdm import tqdm
except ImportError:
    sys.exit("pip install pyodbc tqdm")


def build_model_code(cat, orn):
    """Reconstruct the Odoo model code from CatID and OrnID."""
    cat = re.sub(r'\s+', '', (cat or "").upper())
    orn = re.sub(r'\s+', '', (orn or "").upper()).zfill(3)
    return cat + orn

SERVER   = os.environ.get("MSSQL_SERVER",   "127.0.0.1")
PORT     = int(os.environ.get("MSSQL_PORT", "1433"))
USERNAME = os.environ.get("MSSQL_USER",     "SA")
PASSWORD = os.environ.get("MSSQL_PASSWORD", "Strong@Passw0rd")
OUT_DIR  = os.environ.get("PICTURES_OUT_DIR", "data/pictures")

os.makedirs(OUT_DIR, exist_ok=True)
MANIFEST = os.path.join(OUT_DIR, "manifest.csv")

conn_str = (
    "DRIVER=/usr/lib/x86_64-linux-gnu/odbc/libtdsodbc.so;"
    f"SERVER={SERVER};PORT={PORT};"
    f"UID={USERNAME};PWD={PASSWORD};"
    "TDS_Version=7.4;Encrypt=no;TrustServerCertificate=yes;"
)

print(f"Connecting to {SERVER}:{PORT} …")
try:
    conn = pyodbc.connect(conn_str)
except Exception as e:
    sys.exit(f"Connection failed: {e}")
cursor = conn.cursor()
print("Connected.\n")

manifest_rows = []   # (filename, type, code, cat_id, orn_id, source_date)


def safe_model(code):
    """Sanitize model code for use as a filename."""
    return "".join(c for c in str(code).strip() if c.isalnum() or c in ("-", "_", "."))


def fmt_date(dt):
    """Format a datetime value as ISO string, or empty string."""
    if dt is None:
        return ""
    return str(dt)[:19]


def write_file(filename, blob):
    path = os.path.join(OUT_DIR, filename)
    with open(path, "wb") as f:
        f.write(blob)


# ── TSketches first: high-resolution replacements ─────────────────────────
# TSketches contains only 2 rows (E1514C, P761), both are higher-resolution
# versions of photos already in Sketches.  By exporting them first and using
# the same filename convention ({Model}.jpg), they will take priority over
# the Sketches entry during import (dedup by checksum will replace the lower-
# resolution photo if the model picture is processed again from Sketches).
# We track their model codes so Sketches skips re-exporting a lower-res copy.

print("Exporting high-resolution photos from TSketches.Picture …")
tsketches_model_codes = set()   # models exported from TSketches (photos)
tsketches_drawing_codes = set() # models exported from TSketches (drawings)

cursor.execute("""
    SELECT RTRIM(CatID) AS cat, RTRIM(OrnID) AS orn, RTRIM(Model) AS model,
           Picture, LastUpdated
    FROM PICTURES.dbo.TSketches
    WHERE Picture IS NOT NULL AND DATALENGTH(Picture) > 0
""")
rows = cursor.fetchall()

tsketches_photos = 0
for cat_raw, orn_raw, model_raw, blob, last_updated in tqdm(rows, desc="TSketches photos"):
    cat   = str(cat_raw   or "").strip()
    orn   = str(orn_raw   or "").strip()
    model = str(model_raw or "").strip()
    if not blob:
        continue
    if not model:
        model = build_model_code(cat, orn)
    if not model:
        continue
    fname = f"{safe_model(model)}.jpg"
    write_file(fname, blob)
    manifest_rows.append((fname, "model", model, cat, orn, fmt_date(last_updated)))
    tsketches_model_codes.add(model)
    tsketches_photos += 1

print(f"  → {tsketches_photos} high-res photos from TSketches.\n")

cursor.execute("""
    SELECT RTRIM(CatID) AS cat, RTRIM(OrnID) AS orn, RTRIM(Model) AS model,
           Sketch, LastUpdated
    FROM PICTURES.dbo.TSketches
    WHERE Sketch IS NOT NULL AND DATALENGTH(Sketch) > 0
""")
rows = cursor.fetchall()

tsketches_drawings = 0
for cat_raw, orn_raw, model_raw, blob, last_updated in tqdm(rows, desc="TSketches drawings"):
    cat   = str(cat_raw   or "").strip()
    orn   = str(orn_raw   or "").strip()
    model = str(model_raw or "").strip()
    if not blob:
        continue
    if not model:
        model = build_model_code(cat, orn)
    if not model:
        continue
    fname = f"{safe_model(model)}_drawing.jpg"
    write_file(fname, blob)
    manifest_rows.append((fname, "model_drawing", model, cat, orn, fmt_date(last_updated)))
    tsketches_drawing_codes.add(model)
    tsketches_drawings += 1

print(f"  → {tsketches_drawings} drawings from TSketches.\n")


# ── Sketches: model photos ─────────────────────────────────────────────────

print("Exporting model photos from Sketches.Picture …")
cursor.execute("""
    SELECT RTRIM(CatID) AS cat, RTRIM(OrnID) AS orn, RTRIM(Model) AS model,
           Picture, LastUpdated
    FROM PICTURES.dbo.Sketches
    WHERE Picture IS NOT NULL AND DATALENGTH(Picture) > 0
""")
rows = cursor.fetchall()

photos = skipped = 0
for cat_raw, orn_raw, model_raw, blob, last_updated in tqdm(rows, desc="Model photos"):
    cat   = str(cat_raw   or "").strip()
    orn   = str(orn_raw   or "").strip()
    model = str(model_raw or "").strip()
    if not blob:
        skipped += 1
        continue
    if not model:
        model = build_model_code(cat, orn)
    if not model:
        skipped += 1
        continue
    # Skip models already exported from TSketches at higher resolution
    if model in tsketches_model_codes:
        skipped += 1
        continue
    fname = f"{safe_model(model)}.jpg"
    write_file(fname, blob)
    manifest_rows.append((fname, "model", model, cat, orn, fmt_date(last_updated)))
    photos += 1

print(f"  → {photos} photos, {skipped} skipped (incl. {len(tsketches_model_codes)} replaced by TSketches).\n")


# ── Sketches: drawings ─────────────────────────────────────────────────────

print("Exporting drawings from Sketches.Sketch …")
cursor.execute("""
    SELECT RTRIM(CatID) AS cat, RTRIM(OrnID) AS orn, RTRIM(Model) AS model,
           Sketch, LastUpdated
    FROM PICTURES.dbo.Sketches
    WHERE Sketch IS NOT NULL AND DATALENGTH(Sketch) > 0
""")
rows = cursor.fetchall()

drawings = skipped_d = 0
for cat_raw, orn_raw, model_raw, blob, last_updated in tqdm(rows, desc="Drawings"):
    cat   = str(cat_raw   or "").strip()
    orn   = str(orn_raw   or "").strip()
    model = str(model_raw or "").strip()
    if not blob:
        skipped_d += 1
        continue
    if not model:
        model = build_model_code(cat, orn)
    if not model:
        skipped_d += 1
        continue
    if model in tsketches_drawing_codes:
        skipped_d += 1
        continue
    fname = f"{safe_model(model)}_drawing.jpg"
    write_file(fname, blob)
    manifest_rows.append((fname, "model_drawing", model, cat, orn, fmt_date(last_updated)))
    drawings += 1

print(f"  → {drawings} drawings, {skipped_d} skipped.\n")


# ── Snapshots: product-specific photos ────────────────────────────────────

print("Exporting product photos from Snapshots.Picture …")
cursor.execute("""
    SELECT
        RTRIM(CatID)   AS cat,
        RTRIM(OrnID)   AS orn,
        RTRIM(StoneID) AS stone,
        RTRIM(GoldID)  AS gold,
        Picture,
        LastUpdated
    FROM PICTURES.dbo.Snapshots
    WHERE Picture IS NOT NULL AND DATALENGTH(Picture) > 0
""")
rows = cursor.fetchall()

products_exported = skipped_p = 0
for cat, orn, stone, gold, blob, last_updated in tqdm(rows, desc="Product photos"):
    cat   = str(cat   or "").strip()
    orn   = str(orn   or "").strip()
    stone = str(stone or "").strip()
    gold  = str(gold  or "").strip()
    if not (cat and orn and stone and gold and blob):
        skipped_p += 1
        continue

    # Odoo product code = "{CatID}{OrnID}-{StoneID}/{GoldID}"
    product_code = f"{cat}{orn}-{stone}/{gold}"
    # Safe filename: replace '/' with '~' (unambiguous, reversed in import)
    safe_fname = product_code.replace("/", "~") + ".jpg"

    write_file(safe_fname, blob)
    manifest_rows.append((safe_fname, "product", product_code, cat, orn, fmt_date(last_updated)))
    products_exported += 1

print(f"  → {products_exported} product photos, {skipped_p} skipped.\n")


# ── Write manifest ─────────────────────────────────────────────────────────

with open(MANIFEST, "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["filename", "type", "code", "cat_id", "orn_id", "source_date"])
    w.writerows(manifest_rows)

cursor.close()
conn.close()

total = tsketches_photos + tsketches_drawings + photos + drawings + products_exported
print(f"Done.")
print(f"  TSketches : {tsketches_photos} high-res photos + {tsketches_drawings} drawings")
print(f"  Sketches  : {photos} model photos + {drawings} drawings")
print(f"  Snapshots : {products_exported} product photos")
print(f"  Total     : {total} files + manifest.csv → {OUT_DIR}/")
