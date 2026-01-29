##
#%%
import os
import pyodbc
from tqdm import tqdm

# --- Connexion SQL Server (via FreeTDS sans DSN) --------------------
SERVER   = '127.0.0.1'   # ou 'localhost'
PORT     = 1433
DATABASE = 'PICTURES'
USERNAME = 'SA'
PASSWORD = 'Strong@Passw0rd'

out_dir = 'exported_pictures'

# Chaîne de connexion robuste (pas d'alias de driver, chemin absolu)
conn = pyodbc.connect(
    "DRIVER=/usr/lib/x86_64-linux-gnu/odbc/libtdsodbc.so;"
    f"SERVER={SERVER};PORT={PORT};DATABASE={DATABASE};"
    f"UID={USERNAME};PWD={PASSWORD};"
    "TDS_Version=7.4;"
    "Encrypt=no;"                 # ou: Encrypt=yes;TrustServerCertificate=yes
    "TrustServerCertificate=yes;"
)

cursor = conn.cursor()
# 🔍 Étape 1 : détecter la table et la colonne image
cursor.execute("""
SELECT TABLE_NAME, COLUMN_NAME, DATA_TYPE
FROM INFORMATION_SCHEMA.COLUMNS
WHERE DATA_TYPE IN ('varbinary', 'image');
""")
rows = cursor.fetchall()

print("Binary columns found:")
for t, c, d in rows:
    print(f" - {t}.{c} ({d})")

# 👉 choisis la table et colonne ici :
TABLE_NAME = 'Sketches'
COLUMN_NAME = 'Picture'  # ou 'Sketch' si tu veux les dessins
ID_COLUMNS = ['CatID', 'OrnID', 'Model']  # pour nommer les fichiers

# Construire un identifiant lisible à partir de plusieurs colonnes
query = f"SELECT {', '.join(ID_COLUMNS)}, {COLUMN_NAME} FROM {TABLE_NAME} WHERE {COLUMN_NAME} IS NOT NULL"
cursor.execute(query)

for row in tqdm(cursor, desc="Exporting pictures"):
    *ids, image_data = row
    name = '_'.join(str(i) for i in ids if i is not None)
    name = str(ids[-1])
    filename = os.path.join(out_dir, f"{name}.jpg")
    with open(filename, 'wb') as f:
        f.write(image_data)

print(f"\n📸 Exporting from {TABLE_NAME}.{COLUMN_NAME}")


ID_COLUMNS = ['CatID', 'OrnID', 'Model']  # pour nommer les fichiers

# Construire un identifiant lisible à partir de plusieurs colonnes
cols = ", ".join(ID_COLUMNS + [COLUMN_NAME])
query = f"SELECT {cols} FROM {TABLE_NAME} WHERE {COLUMN_NAME} IS NOT NULL"
cursor.execute(query)


for row in tqdm(cursor, desc="Exporting pictures"):
    *ids, image_data = row  # toutes les colonnes sauf la dernière = identifiants
    name = '_'.join(str(i) for i in ids if i is not None)
    name = [str(i) for i in ids if i is not None][-1]
    
    filename = os.path.join(out_dir, f"{name}.jpg")
    with open(filename, 'wb') as f:
        f.write(image_data)
        

print(f"\n[INFO] Export terminé. Les fichiers sont dans {out_dir}/")

cursor.close()
conn.close()