import os
import pyodbc
from tqdm import tqdm

# --- Configuration ---
SERVER   = '127.0.0.1'
PORT     = 1433
USERNAME = 'SA'
PASSWORD = 'Strong@Passw0rd'
OUT_DIR  = 'exported_drawings'

# Database names
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

# Fetch Sketches (Drawings)
print("Fetching Drawings (Sketches)...")
# We only want rows where Sketch has data (DATALENGTH > 0)
query = f"""
SELECT Model, Sketch 
FROM {DB_PICTURE}.dbo.Sketches 
WHERE DATALENGTH(Sketch) > 0
"""
cursor.execute(query)

count = 0
for row in tqdm(cursor, desc="Exporting Drawings"):
    model_raw, blob = row
    if not blob:
        continue
        
    model = str(model_raw).strip()
    
    # Save as Model Name (e.g. B002.jpg)
    safe_model = model.replace('/', '_').replace('\\', '_')
    safe_model = "".join([c for c in safe_model if c.isalnum() or c in ('-','_','.')])
    
    filename = os.path.join(OUT_DIR, f"{safe_model}.jpg")
    with open(filename, 'wb') as f:
        f.write(blob)
    count += 1

print(f"Done. Exported {count} drawings to {OUT_DIR}.")
conn.close()
