## Legacy SQL Server backups

The three `.bak` files received from Rubicon's server (`JMS-PDP21_<date>.bak`,
`JMS-SIS21_<date>.bak`, `Pictures.bak`) are restored and exported with one
command:

```bash
./ops/migration/restore_mssql.sh all      # or: pdp | sis | pictures
```

The full, ordered rebuild procedure (restore, CSV conversion, Odoo import,
repairs, audits) is documented in `ops/migration/README.md`. Day-to-day
backups of the Odoo database are handled by `ops/backup.sh`.
