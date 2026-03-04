import os
import pyodbc
from tqdm import tqdm
import collections

# --- Configuration ---
SERVER   = '127.0.0.1'
PORT     = 1433
USERNAME = 'SA'
PASSWORD = 'Strong@Passw0rd'
OUT_DIR  = 'exported_pictures_v2'

# Database names
DB_PDP     = 'JMS_PDP21'
DB_PICTURE = 'PICTURES'

if not os.path.exists(OUT_DIR):
    os.makedirs(OUT_DIR)

conn_str = (
    "DRIVER=/usr/lib/x86_64-linux-gnu/odbc/libtdsodbc.so;"
    f"SERVER={SERVER};PORT={PORT};"
    f"UID={USERNAME};PWD={PASSWORD};"
    "TDS_Version=7.4;"
    "Encrypt=no;"
    "TrustServerCertificate=yes;"
)

try:
    conn = pyodbc.connect(conn_str)
    cursor = conn.cursor()
except Exception as e:
    print(f"Connection failed: {e}")
    exit(1)

print("Connected to MSSQL.")

# 1. Fetch Product Mapping (CatID, OrnID -> List of Designs)
# We select from JMS_PDP21
print("Fetching Product list...")
product_map = collections.defaultdict(list)
try:
    cursor.execute(f"SELECT CatID, OrnID, Design FROM {DB_PDP}.dbo.Products")
    rows = cursor.fetchall()
    for cat, orn, design in rows:
        key = (str(cat).strip(), str(orn).strip())
        product_map[key].append(str(design).strip())
    print(f"Loaded {len(rows)} products mapping.")
except Exception as e:
    print(f"Error fetching products: {e}")
    # Proceed? If we can't map, we can only export models.
    
# 2. Fetch Sketches (Model Image)
print("Fetching Sketches...")
query = f"""
SELECT CatID, OrnID, Model, Picture 
FROM {DB_PICTURE}.dbo.Sketches 
WHERE Picture IS NOT NULL
"""
cursor.execute(query)

count = 0
for row in tqdm(cursor, desc="Exporting"):
    cat_raw, orn_raw, model_raw, blob = row
    if not blob:
        continue
        
    cat = str(cat_raw).strip()
    orn = str(orn_raw).strip()
    model = str(model_raw).strip()
    
    # Save as Model Name (e.g. B002.jpg)
    # Sanitize filename
    safe_model = "".join([c for c in model if c.isalnum() or c in ('-','_','.')])
    with open(os.path.join(OUT_DIR, f"{safe_model}.jpg"), 'wb') as f:
        f.write(blob)
    count += 1
    
    # Save as Product Names (e.g. B002-DTS/W.jpg)
    key = (cat, orn)
    designs = product_map.get(key, [])
    for design in designs:
        # Sanitize design (replace / with _ for filesystem)
        safe_design = design.replace('/', '_').replace('\\', '_')
        safe_design = "".join([c for c in safe_design if c.isalnum() or c in ('-','_','.')])
        
        path = os.path.join(OUT_DIR, f"{safe_design}.jpg")
        # Write only if not exists (or overwrite? overwrite is safer to ensure sync)
        with open(path, 'wb') as f:
            f.write(blob)
        count += 1

print(f"Done. Exported {count} files to {OUT_DIR}.")
conn.close()
