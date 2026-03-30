"""
Export photos and drawings from Pictures.bak into data/pictures/.

Sources
-------
PICTURES.dbo.Sketches  (10 656 rows)
  · Picture  → data/pictures/{Model}.jpg          (model photo)
  · Sketch   → data/pictures/{Model}_drawing.jpg  (drawing, 275 rows only)

PICTURES.dbo.Snapshots (250 rows)
  · Picture  → data/pictures/{product_code_safe}.jpg
    where product_code = RTRIM(CatID)+RTRIM(OrnID)+'-'+StoneID+'/'+GoldID
    and   product_code_safe replaces '/' with '~'  (e.g. B001-EMCS+CITA~W.jpg)

A manifest.csv is written alongside the images:
  filename, type, code
  B002.jpg, model, B002
  B002_drawing.jpg, model_drawing, B002
  B001-EMCS+CITA~W.jpg, product, B001-EMCS+CITA/W

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
import sys

try:
    import pyodbc
    from tqdm import tqdm
except ImportError:
    sys.exit("pip install pyodbc tqdm")

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

manifest_rows = []   # (filename, type, code)


def safe_model(code):
    """Sanitize model code for use as a filename."""
    return "".join(c for c in str(code).strip() if c.isalnum() or c in ("-", "_", "."))


def write_file(filename, blob):
    path = os.path.join(OUT_DIR, filename)
    with open(path, "wb") as f:
        f.write(blob)


# ── Sketches: model photos ─────────────────────────────────────────────────

print("Exporting model photos from Sketches.Picture …")
cursor.execute("""
    SELECT Model, Picture
    FROM PICTURES.dbo.Sketches
    WHERE Picture IS NOT NULL AND DATALENGTH(Picture) > 0
""")
rows = cursor.fetchall()

photos = skipped = 0
for model_raw, blob in tqdm(rows, desc="Model photos"):
    model = str(model_raw or "").strip()
    if not model or not blob:
        skipped += 1
        continue
    fname = f"{safe_model(model)}.jpg"
    write_file(fname, blob)
    manifest_rows.append((fname, "model", model))
    photos += 1

print(f"  → {photos} photos, {skipped} skipped.\n")


# ── Sketches: drawings ─────────────────────────────────────────────────────

print("Exporting drawings from Sketches.Sketch …")
cursor.execute("""
    SELECT Model, Sketch
    FROM PICTURES.dbo.Sketches
    WHERE Sketch IS NOT NULL AND DATALENGTH(Sketch) > 0
""")
rows = cursor.fetchall()

drawings = skipped_d = 0
for model_raw, blob in tqdm(rows, desc="Drawings"):
    model = str(model_raw or "").strip()
    if not model or not blob:
        skipped_d += 1
        continue
    fname = f"{safe_model(model)}_drawing.jpg"
    write_file(fname, blob)
    manifest_rows.append((fname, "model_drawing", model))
    drawings += 1

print(f"  → {drawings} drawings, {skipped_d} skipped.\n")


# ── Snapshots: product-specific photos ────────────────────────────────────

print("Exporting product photos from Snapshots.Picture …")
cursor.execute("""
    SELECT
        RTRIM(CatID)  AS cat,
        RTRIM(OrnID)  AS orn,
        StoneID,
        GoldID,
        Picture
    FROM PICTURES.dbo.Snapshots
    WHERE Picture IS NOT NULL AND DATALENGTH(Picture) > 0
""")
rows = cursor.fetchall()

products_exported = skipped_p = 0
for cat, orn, stone, gold, blob in tqdm(rows, desc="Product photos"):
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
    manifest_rows.append((safe_fname, "product", product_code))
    products_exported += 1

print(f"  → {products_exported} product photos, {skipped_p} skipped.\n")


# ── Write manifest ─────────────────────────────────────────────────────────

with open(MANIFEST, "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["filename", "type", "code"])
    w.writerows(manifest_rows)

cursor.close()
conn.close()

total = photos + drawings + products_exported
print(f"Done. {photos} model photos + {drawings} drawings + {products_exported} product photos")
print(f"      → {OUT_DIR}/  ({total} files + manifest.csv)")
