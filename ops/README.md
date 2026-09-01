# ops/ — operating Rubicon Suite

| Path | What it is | Runs on |
|------|------------|---------|
| `backup.sh`, `restore.sh`, `verify_backup.sh`, `healthcheck.sh`, `init_prod.sh` | Stack lifecycle for one environment (`dev`, `demo`, `prod`), always given as first argument | the host running the stack (cron for backup/verify/healthcheck) |
| `lib/common.sh` | Shared environment resolution and helpers sourced by the lifecycle scripts | — |
| `server/` | One-time host provisioning: firewall, TLS / tunnel, VPN, demo hardening, nginx templates | a fresh server, once |
| `migration/` | One-shot rebuild of the Odoo database from the legacy SQL Server `.bak` files. `README.md` there is the runbook | a workstation with Docker and the `.bak` files |
| `dev/` | Developer tooling: OWL error finder, browser console dump, admin password reset for dev databases | a developer machine |
| `SECURITY.md`, `PROD_SETUP.md`, `CRON.md`, `MONITORING.md`, `setup_oci_backup.md` | Operating documentation | — |

## Conventions

- **Bash is only glue.** A shell script here orchestrates external tools
  (`docker compose`, `pg_dump`, `tar`, `age`, `oci`, `ufw`). Anything that
  reads or writes Odoo data is a Python script executed through `odoo shell`
  (the `env` variable is provided) and lives under `migration/` or `dev/`.
- Every shell script starts with `set -euo pipefail`, prints a usage line on
  bad arguments, and passes `shellcheck -S warning` (enforced in CI).
- Lifecycle scripts never guess the environment: `./ops/backup.sh prod`.
  Environment-specific values (compose file, services, database name, backup
  settings) come from `lib/common.sh` and the matching `.env*` file — never
  from hard-coded credentials.
- Destructive actions need an explicit opt-in: `--yes` for restores,
  `RUBICON_ALLOW_*=1` for the migration scripts that wipe or reset data.
- Secrets are read from `.env`, `.env.demo`, `.env.prod` and the Odoo config
  files, all git-ignored (see `SECURITY.md`).
- Logs of unattended runs go next to the data they concern
  (`$BACKUP_DIR/backup.log`, `$BACKUP_DIR/verify.log`), and each run leaves a
  status marker the healthcheck reads.

## Day-to-day

```bash
./ops/healthcheck.sh prod          # what the 5-minute cron runs
./ops/backup.sh prod               # what the nightly cron runs
./ops/verify_backup.sh prod        # what the weekly cron runs
./ops/restore.sh prod latest       # full restore (destructive, asks first)
./ops/restore.sh prod 20260901 --target-db rubicon_inspect --neutralize   # look at an old backup
```
