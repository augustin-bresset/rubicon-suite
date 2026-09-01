# Rebuilding the Odoo database from the legacy SQL Server backups

Use this procedure for a **cold start** (no usable `pg_dump` backup) or a
deliberate re-migration. Since the migration the Odoo database is the source
of truth: day-to-day backup and restore are `ops/backup.sh` and
`ops/restore.sh`, and the tools in this directory are not part of normal
operation.

## Inputs

| File | Content | Size |
|------|---------|------|
| `mssql_backups/JMS-PDP21_<date>.bak` | PDP: models, products, stones, metals, labor, margins | 213 MB |
| `mssql_backups/JMS-SIS21_<date>.bak` | SIS: customers, sales documents and their items | 197 MB |
| `mssql_backups/Pictures.bak` | photos and drawings (`Sketches`, `Snapshots`) | 3.2 GB |
| `mssql_backups/SHA256SUMS` | checksums, created once: `cd mssql_backups && sha256sum *.bak > SHA256SUMS` | |

Keep the three `.bak` files and their checksums off-site, next to the
encrypted database backups: they are the only way back to the pre-Odoo data.

Requirements on the workstation: Docker, Python 3.10+, GNU make, `rsync`,
~10 GB free disk, and the dev stack (`docker compose up -d`).

## Pipeline

```
 .bak ─(1) restore_mssql.sh─► data/backup_pdp/*.csv  data/backup_sis/*.csv  data/pictures/*.jpg + manifest.csv
      ─(2) raw_to_data_*  ─► rubicon_addons/<module>/data/<model>.csv   business data, git-ignored
      ─(3) module install ─► empty database with the curated reference data (CSVs tracked in git)
      ─(4)(6)(7) importers ─► records + filestore
      ─(8) repairs ─(9) audits ─(10) ops/backup.sh
```

Two kinds of data flow through it:

- **Business data** — products, models, product stones, labor costs, parties,
  documents, items, pictures. Regenerated from the `.bak` files; the
  generated CSVs are git-ignored. Verified on 2026-09-01: a fresh export and
  conversion reproduces the CSVs of the original migration byte for byte.
- **Reference data** — stone catalogue, metals, purities, parts, margins,
  labor and addon types, SIS lookups. Generated once, then **curated by hand
  and tracked in git** (whitelisted in `.gitignore`). The converters still
  regenerate them, so step 2 ends by restoring the tracked versions.

## 1. Restore the `.bak` files and export (≈ 1 min for PDP + SIS, longer for pictures)

```bash
./ops/migration/restore_mssql.sh all        # or: pdp | sis | pictures    (= make restore-mssql)
```

Starts `mcr.microsoft.com/mssql/server:2019-latest` on `127.0.0.1:1433` with
a random SA password, verifies the checksums, restores the three databases
(`JMS_PDP21`, `JMS_SIS21`, `PICTURES`), exports every base table with `bcp`
(46 PDP tables, 14 SIS tables) and the images through
`export/export_pictures_products.py`, then removes the container
(`--keep` leaves it running for inspection).

Format details worth knowing: no header, comma separated, `char` columns
padded to their width, CR LF kept inside text fields (the converters re-join
the split rows), NUL bytes stripped (PostgreSQL rejects them). The two
misspelled legacy tables `StoneCatagories` / `ProductCatagories` are exported
under the corrected names the converters use.

## 2. Convert to Odoo CSVs

```bash
make raw_to_data_all      # stone, metal, product, labor, margin  → rubicon_addons/pdp_*/data/
make raw-to-data-sis      # parties and documents                 → rubicon_addons/sis_*/data/
```

Both targets end with `make restore-reference-csvs`, which checks out the
tracked reference CSVs again. Do not skip it: the curated files carry columns
and rows the converters do not know about (e.g. `pdp.metal.csv`
`gold`/`plating`/`purity_system`, removed placeholder categories).

## 3. Fresh database with the reference data

```bash
docker compose up -d
make init-data-modules    # rubicon_env + pdp_stone, pdp_metal, pdp_labor, pdp_margin, pdp_product
```

The tracked reference CSVs are loaded by the module manifests. Run this once
only: a second install of the same modules duplicates reference records
(`cleanup/fix_external_ids.py` exists for that case).

## 4. Import the PDP business data (long: ~250 000 product stones)

```bash
make import_all           # order inside import_csv.py: stone → metal → product → labor → margin
```

Logs go to `meta/logs/import_<timestamp>.log`; "Unresolved Many2one"
warnings list values that exist in the legacy data but not in the curated
reference data — review them, they are the usual source of repairs (step 8).

## 5. Install the applications

```bash
docker compose exec -T odoo odoo -d rubicon -i pdp_frontend,sis_frontend,rubicon_uom,sis_analysis,rubicon_storage --stop-after-init
# plus pcs_frontend,pcs_simulator,ps_utilities,sis_report when those modules are present
```

Never install `rubicon_demo` here: its `pre_init_hook` deletes every product
model, SIS document and partner.

## 6. Import the SIS data

```bash
make import-sis RUBICON_ALLOW_SIS_WIPE=1     # parties, then documents + items (wipes existing SIS documents first)
```

## 7. Import the pictures

```bash
make import-pictures      # data/pictures/manifest.csv → pdp.picture (model photos, drawings, product photos)
```

## 8. Repairs — only when the symptom appears

Run a script with `make shell < ops/migration/cleanup/<script>.py`. They date
from the original migration (March–July 2026); the importers have since
absorbed most of the fixes, so a clean rebuild should need few of them.

| Script | Symptom |
|--------|---------|
| `cleanup/fix_external_ids.py` | duplicated reference records after a double `init-data-modules` |
| `cleanup/cleanup_doc_types.py`, `cleanup_shippers.py`, `cleanup_sis_lookups.py` | duplicated `sis.doc.type` / `sis.shipper` / SIS lookups after a double module upgrade |
| `cleanup/cleanup_margin_duplicates.py`, `restore_margin_subrecords.py` | duplicated `pdp.margin` records versus their XML ids, missing margin sub-records |
| `cleanup/cleanup_none_all.py` | legacy `None` / `All` placeholder records still referenced |
| `cleanup/cleanup_truncated_models.py` | products attached to a model whose code was truncated at import (`P` instead of `P1009`) |
| `import/import_missing_labor.py` | models with no labor cost after `import_all` |
| `cleanup/migrate_sis_product_ids.py` | `sis.document.item.product_id` empty (documents imported before products) |
| `cleanup/restore_doc_flags.py` | closed / cancelled flags lost on `sis.document` |
| `cleanup/migrate_picture_scope.py`, `cleanup_orphan_pictures.py` | pictures imported by an older importer (no scope), orphan pictures |
| `cleanup/update_company.py`, `update_stones.py`, `migrate_total_fob_to_amount.sql` | historic one-offs; not needed on a fresh import |

## 9. Audits

```bash
make audit_counts                                  # record counts → meta/logs/counts_<timestamp>.log
make shell < ops/migration/verify/verify_picture_chain.py
```

Expected orders of magnitude (dev database, 2026-09-01):

| Table | Rows |
|-------|------|
| `pdp_product_model` | 13 056 |
| `pdp_product` | 48 699 |
| `pdp_product_stone` | 247 892 |
| `res_partner` (SIS parties incl. children) | 780 |
| `sis_document` | 18 656 |
| `sis_document_item` | 210 474 |
| `ir_attachment` (pictures) | ≈ 10 300 |

## 10. Back up immediately

```bash
./ops/backup.sh dev       # or prod — the rebuilt database is now the source of truth again
```

## Known limitations

- The generated business CSVs and `data/backup_*` are not versioned; if you
  want to skip steps 1–2 next time, archive them with the `.bak` files
  (`tar czf legacy_csv_<date>.tar.gz data/backup_pdp data/backup_sis`).
- The picture export installs `pyodbc` in a temporary `python:3.11-slim`
  container at each run (network access required).
- Steps 3–8 were last exercised end to end during the original migration;
  steps 1–2 were re-validated on 2026-09-01. Rehearse the whole procedure on
  a scratch machine before relying on it in an emergency.
