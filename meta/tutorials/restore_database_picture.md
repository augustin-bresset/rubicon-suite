# Pictures — Extract from backup and import into Odoo

## Overview

Photos and drawings are stored in a SQL Server database (`Pictures.bak`).
Each photo is linked to a **model** (fallback) and to all **products** of that model via a Many2many relationship.

Workflow:
1. `make export-pictures` — restores `Pictures.bak` and exports JPGs to `data/pictures/`
2. `make import-pictures` — imports `data/pictures/` into Odoo (`pdp.picture`)

---

## Quick start

```bash
# 1. Restore Pictures.bak in a temporary SQL Server and export JPGs + manifest.csv
./ops/migration/restore_mssql.sh pictures          # = make export-pictures
# 2. Import data/pictures/ into Odoo (pdp.picture)
make import-pictures
```

`restore_mssql.sh` needs Docker and `mssql_backups/Pictures.bak`; the SQL
Server container only listens on 127.0.0.1 and is removed afterwards. The
complete rebuild procedure is in `ops/migration/README.md`.

### Step 4 — Import into Odoo

```bash
make import-pictures
# equivalent to:
docker compose exec -T odoo odoo shell -d rubicon --no-http < ops/migration/import/import_pictures.py
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
