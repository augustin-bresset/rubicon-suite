import os
import pyodbc
from tqdm import tqdm

# Configuration de connexion à SQL Server
server = 'localhost,1433'
database = 'PICTURES'
username = 'SA'
password = 'Strong@Passw0rd'

# Répertoire de sortie pour les photos
out_dir = 'exported_pictures'
os.makedirs(out_dir, exist_ok=True)

# Connexion
conn_str = (
    f"DRIVER={{FreeTDS}};"
    f"SERVER={server};DATABASE={database};UID={username};PWD={password};"
    f"TrustServerCertificate=yes;"
)

conn = pyodbc.connect(
    "DSN=sqlsrv;UID=SA;PWD=Strong@Passw0rd;DATABASE=PICTURES;TrustServerCertificate=yes;",
    attrs_before={1256: '/home/smaug/rubicon-suite/freetds.conf'}
)

conn = pyodbc.connect(conn_str)
cursor = conn.cursor()

# 🔍 Étape 1 : détecter la table et la colonne image
cursor.execute("""
SELECT TABLE_NAME, COLUMN_NAME, DATA_TYPE
FROM INFORMATION_SCHEMA.COLUMNS
WHERE DATA_TYPE IN ('varbinary', 'image');
""")
rows = cursor.fetchall()

print("🧠 Binary columns found:")
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
        

print(f"\n✅ Export terminé. Les fichiers sont dans {out_dir}/")

cursor.close()
conn.close()
