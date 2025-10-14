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
    f"DRIVER={{ODBC Driver 18 for SQL Server}};"
    f"SERVER={server};DATABASE={database};UID={username};PWD={password};"
    f"TrustServerCertificate=yes;"
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
TABLE_NAME = rows[0][0]
COLUMN_NAME = rows[0][1]
ID_COLUMN = 'ID'  # adapte si ta table a un autre identifiant

print(f"\n📸 Exporting from {TABLE_NAME}.{COLUMN_NAME}")

# 🔄 Étape 2 : export
query = f"SELECT {ID_COLUMN}, {COLUMN_NAME} FROM {TABLE_NAME} WHERE {COLUMN_NAME} IS NOT NULL"
cursor.execute(query)

for record_id, image_data in tqdm(cursor, desc="Exporting pictures"):
    filename = os.path.join(out_dir, f"{record_id}.jpg")
    with open(filename, 'wb') as f:
        f.write(image_data)

print(f"\n✅ Export terminé. Les fichiers sont dans {out_dir}/")

cursor.close()
conn.close()
