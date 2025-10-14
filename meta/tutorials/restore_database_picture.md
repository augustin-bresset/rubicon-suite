# Tutoriel : Récupérer et intégrer les images de `Pictures.bak` dans Odoo

---

## 1  Objectif

L’ancien logiciel PDP stockait ses images (dessins, modèles, croquis, etc.) dans une base SQL Server appelée `Pictures`.
L’objectif est de :

* restaurer cette base `.bak` dans un conteneur SQL Server,
* extraire les images réelles sur disque,
* puis les importer proprement dans Odoo (via un module `pdp_picture`).

---

## 2  Restaurer la base `Pictures.bak`

### Étape 1 – Créer le conteneur SQL Server

Dans ton dossier de projet (ex. `~/rubicon-suite/`), tu dois avoir ton backup :

```
mssql_backups/Pictures.bak
```

Lance un conteneur SQL Server avec ce dossier monté :

```bash
docker rm -f sqlsrv
docker run -d \
  --name sqlsrv \
  -e "ACCEPT_EULA=Y" \
  -e "SA_PASSWORD=Strong@Passw0rd" \
  -p 1433:1433 \
  -v /home/smaug/rubicon-suite/mssql_backups:/var/opt/mssql/backup \
  mcr.microsoft.com/mssql/server:2019-latest
```

---

### Étape 2 – Vérifier que le backup est visible

```bash
docker exec -it sqlsrv ls -lh /var/opt/mssql/backup
```

→ tu dois voir `Pictures.bak`.

---

### Étape 3 – Identifier les fichiers logiques

```bash
docker exec -it sqlsrv /opt/mssql-tools18/bin/sqlcmd \
  -S localhost -U SA -P 'Strong@Passw0rd' -C \
  -Q "RESTORE FILELISTONLY FROM DISK = '/var/opt/mssql/backup/Pictures.bak';"
```

Tu obtiens par exemple :

```
LogicalName      PhysicalName
-----------------------------------------------
Pictures_Data    C:\Program Files\...\Pictures.mdf
Pictures_Log     C:\Program Files\...\Pictures_0.ldf
```

---

### Étape 4 – Restaurer la base

```bash
docker exec -it sqlsrv /opt/mssql-tools18/bin/sqlcmd \
  -S localhost -U SA -P 'Strong@Passw0rd' -C \
  -Q "RESTORE DATABASE PICTURES
      FROM DISK = '/var/opt/mssql/backup/Pictures.bak'
      WITH 
        MOVE 'Pictures_Data' TO '/var/opt/mssql/data/Pictures.mdf',
        MOVE 'Pictures_Log'  TO '/var/opt/mssql/data/Pictures_log.ldf',
        REPLACE;"
```

---

### Étape 5 – Vérifier la restauration

```bash
docker exec -it sqlsrv /opt/mssql-tools18/bin/sqlcmd \
  -S localhost -U SA -P 'Strong@Passw0rd' -C \
  -Q "SELECT name FROM sys.databases;"
```

Tu devrais voir `PICTURES`.

---

## 3 Exporter les images depuis SQL Server

### Étape 1 – Lancer un conteneur Python temporaire

On utilise un conteneur Python pour extraire les images sans rien installer sur ta machine :

```bash
docker run -it --rm \
  --network=host \
  -v "$PWD":/app \
  python:3.11-slim bash
```

---

### Étape 2 – Installer les dépendances dans le conteneur

```bash
apt update && apt install -y unixodbc unixodbc-dev freetds-dev tdsodbc gcc g++
pip install pyodbc tqdm
cd /app
```

---

### Étape 3 – Créer le script `export_pictures.py`

Dans ton dossier `/app` (donc `rubicon-suite` sur ton hôte) :

```python
import os
import pyodbc
from tqdm import tqdm

server = 'localhost,1433'
database = 'PICTURES'
username = 'SA'
password = 'Strong@Passw0rd'

out_dir = 'exported_pictures/Sketches'
os.makedirs(out_dir, exist_ok=True)

conn = pyodbc.connect(
    f"DRIVER={{FreeTDS}};"
    f"SERVER={server};DATABASE={database};UID={username};PWD={password};"
    f"TrustServerCertificate=yes;"
)
cursor = conn.cursor()

TABLE_NAME = 'Sketches'
COLUMN_NAME = 'Picture'
ID_COLUMNS = ['CatID', 'OrnID', 'Model']

cols = ", ".join(ID_COLUMNS + [COLUMN_NAME])
query = f"SELECT {cols} FROM {TABLE_NAME} WHERE {COLUMN_NAME} IS NOT NULL"
cursor.execute(query)

for row in tqdm(cursor, desc="Exporting pictures"):
    *ids, image_data = row
    name = '_'.join(str(i) for i in ids if i is not None)
    filename = os.path.join(out_dir, f"{name}.jpg")
    with open(filename, 'wb') as f:
        f.write(image_data)

cursor.close()
conn.close()
print(f"✅ Export terminé. Les fichiers sont dans {out_dir}/")
```

---

### Étape 4 – Exécuter le script

```bash
python3 export_pictures.py
```

👉 Les fichiers `.jpg` sont exportés dans `rubicon-suite/exported_pictures/Sketches/`.

---

## 4️⃣  Intégrer les images dans Odoo

### Étape 1 – Créer le module `pdp_picture`

Dans `rubicon_addons/pdp_picture/` :

#### `__manifest__.py`

```python
{
    "name": "PDP Picture",
    "version": "1.0",
    "depends": ["pdp_model", "pdp_ornament"],
    "data": [
        "security/ir.model.access.csv",
        "views/picture_views.xml",
    ],
    "installable": True,
}
```

### Étape 2 – Importer les images extraites dans Odoo

Exécute dans l’Odoo shell :

```bash
docker compose exec -T odoo odoo shell -d rubicon
```

Puis :

```python
import os, base64
Picture = env['pdp.picture']
base_path = '/mnt/extra-addons/pictures/Sketches'

for filename in os.listdir(base_path):
    if not filename.lower().endswith('.jpg'):
        continue
    name = filename.replace('.jpg', '')
    with open(os.path.join(base_path, filename), 'rb') as f:
        Picture.create({
            'name': name,
            'sketch_type': 'model',
            'picture': base64.b64encode(f.read()),
        })
```

---

