"""
Diagnostic: how the old PICTURES database links to the current Odoo database.

Tables analysed
---------------
PICTURES.dbo.Sketches   – model photos + drawings
PICTURES.dbo.Snapshots  – product-specific photos
PICTURES.dbo.TSketches  – alternate/temp sketches (structure same as Sketches)

For each table the script tries every plausible matching strategy and reports
hit/miss counts so we know which approach works for the import pipeline.

Run (standalone, outside Odoo):
  python3 ops/audit/audit_pictures_linkage.py

Prerequisites:
  pip install pyodbc psycopg2-binary
  SQL Server container 'sqlsrv' running with Pictures.bak restored.
"""

import os
import re
import sys

# ── Check dependencies ─────────────────────────────────────────────────────
try:
    import pyodbc
except ImportError:
    sys.exit("Missing: pip install pyodbc")
try:
    import psycopg2
    import psycopg2.extras
except ImportError:
    sys.exit("Missing: pip install psycopg2-binary")


# ── Connection settings ────────────────────────────────────────────────────
MSSQL_SERVER   = os.environ.get("MSSQL_SERVER",   "127.0.0.1")
MSSQL_PORT     = int(os.environ.get("MSSQL_PORT", "1433"))
MSSQL_USER     = os.environ.get("MSSQL_USER",     "SA")
MSSQL_PASSWORD = os.environ.get("MSSQL_PASSWORD", "Strong@Passw0rd")
MSSQL_DB       = os.environ.get("MSSQL_DB",       "PICTURES")

PG_HOST        = os.environ.get("PG_HOST",     "localhost")
PG_PORT        = int(os.environ.get("PG_PORT", "5432"))
PG_DB          = os.environ.get("PG_DB",       "rubicon")
PG_USER        = os.environ.get("PG_USER",     "rubicondev")
PG_PASSWORD    = os.environ.get("PG_PASSWORD", "passwd")


# ── Helpers (mirrors rubicon_import/tools/standard.py) ────────────────────

def create_model_code(category: str, orn_id: str) -> str:
    """Reproduce the Odoo model code from CatID + OrnID."""
    code = (category.strip() + orn_id.strip().zfill(3)).upper()
    return re.sub(r'[ ]', '', code)


def section(title: str):
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


# ── Connect ────────────────────────────────────────────────────────────────

print("Connecting to SQL Server …")
mssql_conn = pyodbc.connect(
    "DRIVER=/usr/lib/x86_64-linux-gnu/odbc/libtdsodbc.so;"
    f"SERVER={MSSQL_SERVER};PORT={MSSQL_PORT};DATABASE={MSSQL_DB};"
    f"UID={MSSQL_USER};PWD={MSSQL_PASSWORD};"
    "TDS_Version=7.4;Encrypt=no;TrustServerCertificate=yes;"
)
mssql = mssql_conn.cursor()
print("  SQL Server OK")

print("Connecting to PostgreSQL …")
pg_conn = psycopg2.connect(
    host=PG_HOST, port=PG_PORT,
    dbname=PG_DB, user=PG_USER, password=PG_PASSWORD
)
pg = pg_conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
print("  PostgreSQL OK\n")


# ── Load Odoo reference sets ───────────────────────────────────────────────

section("Loading Odoo reference data")

pg.execute("SELECT id, code, drawing FROM pdp_product_model")
odoo_models = pg.fetchall()
odoo_model_by_code    = {r["code"]: r for r in odoo_models}
odoo_model_by_drawing = {}
for r in odoo_models:
    d = (r["drawing"] or "").strip()
    if d:
        odoo_model_by_drawing.setdefault(d, []).append(r)
print(f"  pdp.product.model : {len(odoo_models)} records")
print(f"  Unique drawing refs in Odoo : {len(odoo_model_by_drawing)}")

pg.execute("SELECT id, code FROM pdp_product")
odoo_products   = pg.fetchall()
odoo_product_by_code = {r["code"]: r for r in odoo_products}
print(f"  pdp.product       : {len(odoo_products)} records")


# ── Specific example given by user ─────────────────────────────────────────

section("Specific example: R132 / drawing RP128B")
example_model_code   = "R132"
example_drawing_ref  = "RP128B"

m_by_code = odoo_model_by_code.get(example_model_code)
print(f"  Model '{example_model_code}' found by code?    {bool(m_by_code)}  → {m_by_code}")

m_by_drawing = odoo_model_by_drawing.get(example_drawing_ref, [])
print(f"  Drawing '{example_drawing_ref}' found?         {bool(m_by_drawing)}  → {m_by_drawing[:2]}")

# Check what Sketches says for R132
mssql.execute("""
    SELECT TOP 5 CatID, OrnID, Model, LastUpdated,
           DATALENGTH(Picture) AS pic_size,
           DATALENGTH(Sketch)  AS sketch_size
    FROM Sketches
    WHERE RTRIM(CatID) = 'R' AND RTRIM(OrnID) LIKE '132%'
""")
rows = mssql.fetchall()
print(f"\n  Sketches rows for CatID=R OrnID=132*:")
for r in rows:
    cat, orn, model, upd, psz, ssz = r
    built = create_model_code(cat or "", orn or "")
    print(f"    CatID={repr(cat)} OrnID={repr(orn)} Model={repr(model)}"
          f"  built_code={built}  pic={psz}B  sketch={ssz}B  upd={upd}")

if not rows:
    print("    (no rows found - check OrnID padding or CatID value)")


# ── Sketches table analysis ────────────────────────────────────────────────

section("Sketches – schema and sample rows")

mssql.execute("""
    SELECT COLUMN_NAME, DATA_TYPE, CHARACTER_MAXIMUM_LENGTH
    FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_NAME = 'Sketches'
    ORDER BY ORDINAL_POSITION
""")
cols = mssql.fetchall()
print("  Columns:")
for c in cols:
    print(f"    {c[0]:20s}  {c[1]}({c[2]})")

mssql.execute("""
    SELECT TOP 10
        RTRIM(CatID)  AS cat,
        RTRIM(OrnID)  AS orn,
        Model,
        DATALENGTH(Picture) AS pic_bytes,
        DATALENGTH(Sketch)  AS sketch_bytes
    FROM Sketches
    WHERE Picture IS NOT NULL
    ORDER BY NEWID()
""")
rows = mssql.fetchall()
print("\n  Sample rows (random 10):")
print(f"  {'Cat':4s} {'Orn':8s} {'Model':8s} {'PicBytes':10s} {'SketchBytes':12s} {'BuiltCode':10s}")
for cat, orn, model, pb, sb in rows:
    built = create_model_code(cat or "", orn or "")
    print(f"  {str(cat):4s} {str(orn):8s} {str(model):8s} {str(pb or 0):10s} {str(sb or 0):12s} {built:10s}")


# ── Sketches: matching strategy comparison ─────────────────────────────────

section("Sketches – matching strategy comparison")

mssql.execute("""
    SELECT RTRIM(CatID) AS cat, RTRIM(OrnID) AS orn, RTRIM(Model) AS model
    FROM Sketches
    WHERE Picture IS NOT NULL OR Sketch IS NOT NULL
""")
all_sketches = mssql.fetchall()
total = len(all_sketches)
print(f"  Total Sketches rows with Picture or Sketch: {total}")

hit_by_built_code = 0   # cat+orn → odoo model code
hit_by_model_code = 0   # Model field → odoo model code
hit_by_drawing    = 0   # Model field → odoo model.drawing

miss_examples_built = []
miss_examples_model_code = []
miss_examples_drawing = []

for cat, orn, model in all_sketches:
    built = create_model_code(cat or "", orn or "")
    model_stripped = (model or "").strip()

    if built in odoo_model_by_code:
        hit_by_built_code += 1
    elif len(miss_examples_built) < 5:
        miss_examples_built.append((cat, orn, built))

    if model_stripped in odoo_model_by_code:
        hit_by_model_code += 1
    elif len(miss_examples_model_code) < 5:
        miss_examples_model_code.append((cat, orn, model_stripped))

    if model_stripped in odoo_model_by_drawing:
        hit_by_drawing += 1
    elif len(miss_examples_drawing) < 5:
        miss_examples_drawing.append((cat, orn, model_stripped))

pct = lambda n: f"{n}/{total} ({100*n//total if total else 0}%)"

print(f"\n  Strategy A: create_model_code(CatID, OrnID) → model.code")
print(f"    Hits: {pct(hit_by_built_code)}")
if miss_examples_built:
    print(f"    Miss examples: {miss_examples_built}")

print(f"\n  Strategy B: Model field → model.code (direct)")
print(f"    Hits: {pct(hit_by_model_code)}")
if miss_examples_model_code:
    print(f"    Miss examples: {miss_examples_model_code}")

print(f"\n  Strategy C: Model field → model.drawing")
print(f"    Hits: {pct(hit_by_drawing)}")
if miss_examples_drawing:
    print(f"    Miss examples: {miss_examples_drawing}")

# Check: is there overlap (same row matches multiple strategies)?
section("Sketches – combined strategy analysis")
both_A_and_C = 0
only_A = 0
only_C = 0
neither = 0

for cat, orn, model in all_sketches:
    built = create_model_code(cat or "", orn or "")
    model_s = (model or "").strip()
    a = built in odoo_model_by_code
    c = model_s in odoo_model_by_drawing
    if a and c:
        both_A_and_C += 1
    elif a:
        only_A += 1
    elif c:
        only_C += 1
    else:
        neither += 1

print(f"  Matches both A and C : {both_A_and_C}")
print(f"  Only A (cat+orn code) : {only_A}")
print(f"  Only C (drawing ref)  : {only_C}")
print(f"  Neither               : {neither}")


# ── TSketches analysis ─────────────────────────────────────────────────────

section("TSketches – comparison with Sketches")

try:
    mssql.execute("SELECT COUNT(*) FROM TSketches")
    t_count = mssql.fetchone()[0]

    mssql.execute("""
        SELECT COUNT(*) FROM TSketches WHERE Picture IS NOT NULL
    """)
    t_pic = mssql.fetchone()[0]

    mssql.execute("""
        SELECT COUNT(*) FROM TSketches WHERE Sketch IS NOT NULL
    """)
    t_sk = mssql.fetchone()[0]

    print(f"  TSketches total rows: {t_count}")
    print(f"  Rows with Picture   : {t_pic}")
    print(f"  Rows with Sketch    : {t_sk}")

    # Are there rows in TSketches NOT in Sketches?
    mssql.execute("""
        SELECT COUNT(*) FROM TSketches T
        WHERE NOT EXISTS (
            SELECT 1 FROM Sketches S
            WHERE RTRIM(S.CatID)=RTRIM(T.CatID) AND RTRIM(S.OrnID)=RTRIM(T.OrnID)
        )
    """)
    t_only = mssql.fetchone()[0]
    print(f"  Rows in TSketches but NOT in Sketches: {t_only}")

    # Are there rows in Sketches NOT in TSketches?
    mssql.execute("""
        SELECT COUNT(*) FROM Sketches S
        WHERE NOT EXISTS (
            SELECT 1 FROM TSketches T
            WHERE RTRIM(S.CatID)=RTRIM(T.CatID) AND RTRIM(S.OrnID)=RTRIM(T.OrnID)
        )
    """)
    s_only = mssql.fetchone()[0]
    print(f"  Rows in Sketches but NOT in TSketches: {s_only}")

    # Sample TSketches-only rows
    if t_only > 0:
        mssql.execute("""
            SELECT TOP 5 RTRIM(T.CatID) AS cat, RTRIM(T.OrnID) AS orn, T.Model,
                   DATALENGTH(T.Picture) AS pb
            FROM TSketches T
            WHERE NOT EXISTS (
                SELECT 1 FROM Sketches S
                WHERE RTRIM(S.CatID)=RTRIM(T.CatID) AND RTRIM(S.OrnID)=RTRIM(T.OrnID)
            ) AND T.Picture IS NOT NULL
        """)
        t_only_rows = mssql.fetchall()
        print(f"  Sample TSketches-only rows:")
        for cat, orn, model, pb in t_only_rows:
            built = create_model_code(cat or "", orn or "")
            in_odoo = built in odoo_model_by_code
            print(f"    {cat} {orn} model={model} built={built} in_odoo={in_odoo} pic={pb}B")

except Exception as e:
    print(f"  TSketches query failed: {e}")


# ── Snapshots analysis ─────────────────────────────────────────────────────

section("Snapshots – schema and sample rows")

try:
    mssql.execute("""
        SELECT COLUMN_NAME, DATA_TYPE, CHARACTER_MAXIMUM_LENGTH
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_NAME = 'Snapshots'
        ORDER BY ORDINAL_POSITION
    """)
    cols = mssql.fetchall()
    print("  Columns:")
    for c in cols:
        print(f"    {c[0]:20s}  {c[1]}({c[2]})")

    mssql.execute("""
        SELECT COUNT(*) FROM Snapshots WHERE Picture IS NOT NULL
    """)
    snap_total = mssql.fetchone()[0]
    print(f"\n  Snapshots rows with Picture: {snap_total}")

    mssql.execute("""
        SELECT TOP 10
            RTRIM(CatID) AS cat,
            RTRIM(OrnID) AS orn,
            RTRIM(StoneID) AS stone,
            RTRIM(GoldID)  AS gold,
            DATALENGTH(Picture) AS pb
        FROM Snapshots
        WHERE Picture IS NOT NULL
        ORDER BY NEWID()
    """)
    rows = mssql.fetchall()
    print(f"\n  Sample rows:")
    print(f"  {'Cat':4s} {'Orn':8s} {'StoneID':16s} {'GoldID':8s} {'PicBytes':10s} {'BuiltCode':12s} {'InOdoo':8s}")
    for cat, orn, stone, gold, pb in rows:
        built_model = create_model_code(cat or "", orn or "")
        product_code = f"{(cat or '').strip()}{(orn or '').strip()}-{(stone or '').strip()}/{(gold or '').strip()}"
        in_odoo = product_code in odoo_product_by_code
        print(f"  {str(cat):4s} {str(orn):8s} {str(stone):16s} {str(gold):8s} "
              f"{str(pb or 0):10s} {built_model:12s} {str(in_odoo):8s}"
              f"  product_code={product_code}")

    # Match rate for Snapshots
    mssql.execute("""
        SELECT RTRIM(CatID) AS cat, RTRIM(OrnID) AS orn,
               RTRIM(StoneID) AS stone, RTRIM(GoldID) AS gold
        FROM Snapshots
        WHERE Picture IS NOT NULL
    """)
    all_snaps = mssql.fetchall()
    snap_hit = 0
    snap_miss_examples = []
    for cat, orn, stone, gold in all_snaps:
        product_code = f"{(cat or '').strip()}{(orn or '').strip()}-{(stone or '').strip()}/{(gold or '').strip()}"
        if product_code in odoo_product_by_code:
            snap_hit += 1
        elif len(snap_miss_examples) < 8:
            snap_miss_examples.append(product_code)

    total_snaps = len(all_snaps)
    pct_s = f"{snap_hit}/{total_snaps} ({100*snap_hit//total_snaps if total_snaps else 0}%)"
    print(f"\n  Snapshot → product match rate: {pct_s}")
    if snap_miss_examples:
        print(f"  Miss examples:")
        for ex in snap_miss_examples:
            print(f"    {ex}")

except Exception as e:
    print(f"  Snapshots query failed: {e}")


# ── Models in Odoo without drawing ref ────────────────────────────────────

section("Odoo models: drawing field coverage")

pg.execute("SELECT COUNT(*) FROM pdp_product_model WHERE drawing IS NOT NULL AND drawing != ''")
with_drawing = pg.fetchone()[0]
pg.execute("SELECT COUNT(*) FROM pdp_product_model")
total_models = pg.fetchone()[0]
print(f"  Models with drawing ref : {with_drawing}/{total_models}")

# How many drawing refs in Odoo match Sketches.Model?
all_odoo_drawings = set(odoo_model_by_drawing.keys())
mssql.execute("SELECT DISTINCT RTRIM(Model) FROM Sketches WHERE Model IS NOT NULL")
all_sketch_models = {r[0].strip() for r in mssql.fetchall() if r[0]}
in_both = all_odoo_drawings & all_sketch_models
print(f"  Drawing refs in Odoo that appear in Sketches.Model: {len(in_both)}/{len(all_odoo_drawings)}")
if len(all_sketch_models) - len(in_both) > 0:
    orphan_sketches = all_sketch_models - all_odoo_drawings
    print(f"  Sketches.Model values NOT in Odoo drawing field: {len(orphan_sketches)}")
    print(f"  Sample orphans: {sorted(orphan_sketches)[:10]}")


# ── Current pipeline state ─────────────────────────────────────────────────

section("Current pipeline state: manifest.csv")

MANIFEST = "data/pictures/manifest.csv"
if os.path.isfile(MANIFEST):
    import csv
    with open(MANIFEST) as f:
        rows = list(csv.DictReader(f))
    types = {}
    for r in rows:
        types[r["type"]] = types.get(r["type"], 0) + 1
    print(f"  manifest.csv found: {len(rows)} entries")
    for t, n in sorted(types.items()):
        print(f"    {t:20s}: {n}")

    # Check how many manifest codes resolve in Odoo
    model_rows  = [r for r in rows if r["type"] in ("model", "model_drawing")]
    product_rows = [r for r in rows if r["type"] == "product"]

    model_hit = sum(1 for r in model_rows if r["code"].strip() in odoo_model_by_code)
    model_miss = len(model_rows) - model_hit
    print(f"\n  Manifest model/model_drawing rows: {len(model_rows)}")
    print(f"    Matching by model.code : {model_hit} hit, {model_miss} miss")

    # Try matching by drawing instead
    model_hit_draw = sum(1 for r in model_rows if r["code"].strip() in odoo_model_by_drawing)
    print(f"    Matching by model.drawing : {model_hit_draw} hit")

    product_hit = sum(1 for r in product_rows if r["code"].strip() in odoo_product_by_code)
    print(f"\n  Manifest product rows : {len(product_rows)}")
    print(f"    Matching by product.code : {product_hit} hit, {len(product_rows)-product_hit} miss")
else:
    print(f"  manifest.csv not found at {MANIFEST} (run make export-pictures first)")


# ── Summary & Recommendations ──────────────────────────────────────────────

section("SUMMARY & RECOMMENDATIONS")
print("""
  The old database contains:

  1. Sketches   – ~10 656 rows: one row per ornament (CatID+OrnID).
                  · Picture  = model thumbnail photo
                  · Sketch   = technical drawing
                  · Model    = 'drawing reference' (e.g. RP128B)
                               → matches pdp.product.model.drawing in Odoo
                               → does NOT match pdp.product.model.code (= cat+orn)

  2. Snapshots  – ~250 rows: one row per product variant.
                  · Picture  = product-specific photo
                  · Product code = CatID+OrnID-StoneID/GoldID
                               → should match pdp.product.code in Odoo

  3. TSketches  – same structure as Sketches (see counts above).
                  Check report above to decide if it adds extra rows.

  Current pipeline issue (if confirmed above):
  ─────────────────────────────────────────────
  export_pictures_products.py  writes manifest with code = Sketches.Model ("RP128B")
  import_pictures.py           searches by pdp.product.model.code ("R132")
  → match rate = 0% for model photos/drawings

  Recommended fix for export_pictures_products.py:
  ─────────────────────────────────────────────────
  In Sketches export, use:
      code = create_model_code(RTRIM(CatID), RTRIM(OrnID))
  instead of:
      code = RTRIM(Model)

  And keep the filename as Model-based (for uniqueness):
      photo   → {Model}.jpg            (same as now)
      drawing → {Model}_drawing.jpg    (same as now)
  but write code = "R132" in the manifest, not "RP128B".

  This matches Strategy A which should have the highest hit rate.
""")

mssql_conn.close()
pg_conn.close()
print("Done.")
