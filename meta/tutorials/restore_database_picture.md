# Pictures — Extract from backup and import into Odoo

## Overview

Photos and drawings are stored in a SQL Server database (`Pictures.bak`).
Each photo is linked to a **model** (fallback) and to all **products** of that model via a Many2many relationship.

Workflow:
1. `make export-pictures` — restores `Pictures.bak` and exports JPGs to `data/pictures/`
2. `make import-pictures` — imports `data/pictures/` into Odoo (`pdp.picture`)

---

## Quick start (automated)

```bash
# Full pipeline: restore backup → export JPGs → import into Odoo
make export-pictures
make import-pictures
```

`export-pictures` requires Docker and `mssql_backups/Pictures.bak`.

---

## Manual steps (if the Makefile targets don't work)

### Step 1 — Start SQL Server container

```bash
docker run -d --name sqlsrv \
  -e "ACCEPT_EULA=Y" -e "SA_PASSWORD=Strong@Passw0rd" \
  -p 1433:1433 \
  -v $(pwd)/mssql_backups:/var/opt/mssql/backup \
  mcr.microsoft.com/mssql/server:2019-latest
sleep 20
```

### Step 2 — Restore the backup

```bash
docker exec sqlsrv /opt/mssql-tools18/bin/sqlcmd \
  -S localhost -U SA -P 'Strong@Passw0rd' -C \
  -Q "RESTORE DATABASE PICTURES
      FROM DISK = '/var/opt/mssql/backup/Pictures.bak'
      WITH MOVE 'Pictures_Data' TO '/var/opt/mssql/data/Pictures.mdf',
           MOVE 'Pictures_Log'  TO '/var/opt/mssql/data/Pictures_log.ldf',
      REPLACE;"
```

### Step 3 — Export photos and drawings

Run inside a temporary Python container (no local install needed):

```bash
docker run --rm --network=host \
  -v $(pwd):/app \
  -e PICTURES_OUT_DIR=/app/data/pictures \
  python:3.11-slim bash -c "
    apt-get update -qq && apt-get install -y -qq unixodbc unixodbc-dev freetds-dev tdsodbc gcc > /dev/null 2>&1
    pip install -q pyodbc tqdm
    cd /app && python3 ops/export/export_pictures_products.py"
```

Output files:
- `data/pictures/{Model}.jpg` — model photo
- `data/pictures/{Model}_drawing.jpg` — drawing/sketch for that model

### Step 4 — Import into Odoo

```bash
make import-pictures
# equivalent to:
docker compose exec -T odoo odoo shell -d rubicon --no-http < ops/import/import_pictures.py
```

The import script:
- Matches `{Model}.jpg` against `pdp.product.model.code`
- Creates one `pdp.picture` per model with `model_id` set
- Links all products of that model via `product_ids` (Many2many)
- Adds `drawing_1920` from `{Model}_drawing.jpg` to the same record
- Deduplicates by MD5 checksum (no duplicate records)

---

## Data model

```
pdp.picture
  model_id    → pdp.product.model   (fallback; shown if no product-specific picture)
  product_ids → pdp.product (M2M)   (primary link; unlink = remove from M2M, record stays)
  image_1920  — product/model photo
  drawing_1920 — sketch/drawing
```

**Deleting a picture from a product** removes the product from `product_ids` only.
The `pdp.picture` record is deleted automatically only if it has no remaining links
(no `model_id` and empty `product_ids`).

---

## Cleanup

Old extracted directories (`exported_pictures/`, `exported_pictures_v2/`, `exported_drawings/`) at the repo root are obsolete and can be deleted:

```bash
rm -rf exported_pictures exported_pictures_v2 exported_drawings
```

The canonical output directory is `data/pictures/` (mounted into Odoo at `/mnt/extra-addons/pictures`).
