# Security — Rubicon Suite

## Environments

| Environment | Where | Reachable from | TLS | Firewall |
|-------------|-------|----------------|-----|----------|
| dev (`docker-compose.yml`) | developer machine, `localhost:8069` | local only | no | none |
| demo (`docker-compose.demo.yml`) | cloud VPS, `127.0.0.1:8070` | Internet through a Cloudflare tunnel | Cloudflare | `setup_firewall.sh demo` |
| prod (`docker-compose.prod.yml`) | cloud VPS, `127.0.0.1:8069` + `8072` | Internet through nginx + Let's Encrypt (or a named Cloudflare tunnel) | yes | `harden_server.sh` + `setup_firewall.sh online` |

An on-premises variant (Odoo on a LAN, remote staff over WireGuard) remains
available with `setup_firewall.sh lan`, `setup_wireguard.sh` and
`add_vpn_user.sh`; it is not the target architecture.

The step-by-step go-live procedure is `ops/PROD_SETUP.md`.

## Network model (prod)

```
Internet ──443──► nginx (TLS, HSTS, rate limit on /web/login, /web/database/ blocked)
                    ├── / ─────────► 127.0.0.1:8069  odoo (workers)
                    └── /websocket ► 127.0.0.1:8072  odoo (gevent)
                                        └── db:5432   postgres (compose network only, never published)
```

- Odoo and PostgreSQL are never bound to a public interface. Docker's port
  publishing bypasses UFW, so **binding to 127.0.0.1 in the compose file is the
  real control**, the firewall is the second line.
- `proxy_mode = True` makes Odoo trust `X-Forwarded-*` only because nginx is
  the sole client of 8069.

## Odoo hardening (odoo.prod.conf)

| Setting | Effect |
|---------|--------|
| `list_db = False` | no database list, database manager disabled |
| `dbfilter = ^rubicon$`, `db_name = rubicon` | only the production database is served; crons run on it alone |
| `admin_passwd` (48 hex chars) | master password of the (disabled) manager — still required to be strong |
| `workers = 2`, `limit_*` | request isolation, CPU / memory / time limits per request |
| no `logfile` | logs reach `docker compose logs` and are rotated by Docker |
| `rubicon_demo` never installed | its `pre_init_hook` deletes products, documents and partners |

Application side: two-factor authentication for every user (Preferences ›
Account Security), one named account per person, no shared administrator.

## Access control

Odoo groups defined in `rubicon_env/security/security.xml`. Every Rubicon
model has three access levels; an internal user gets **read** by default and
must be added to a group to write:

| Group | Rights on PDP / SIS / PCS models | Typical people |
|-------|----------------------------------|----------------|
| Rubicon / User (implied by *Internal user*) | read | everyone with a login |
| Rubicon / Production Operator | read everywhere + write the production floor records (PCS transactions, SSP, clearances, barcode tags) | quality controllers, lapidary supervisors, workshop |
| Rubicon / Editor | read, create, write | designers, officers, buyers, stock |
| Rubicon / Manager | read, create, write, **delete** | director, manager, administrators |

The role groups (Director, Team Manager, Officer, Product Designer, Stone
Buyer, Metal Buyer, Stock Manager, Accountant, Quality Controller, Lapidary
Supervisor — table in `meta/security.md`, matching the job descriptions of
`meta/audit.pdf` §2.3) imply one of the levels;
assign the role, not the level. Upgrading to `rubicon_env` 18.0.1.1 grants
Editor to every existing internal user so nobody is locked out at deploy time.
Configuration models (`pdp.config`, units of measure, roles) stay
administrator-only.

## Host hardening (prod and demo VPS)

```bash
./ops/server/harden_server.sh            # SSH key-only, fail2ban (sshd + nginx-limit-req), unattended-upgrades
./ops/server/setup_firewall.sh online    # 22 (optionally SSH_ALLOW_FROM=<cidr>), 80, 443
```

Mirror the same three ports in the cloud provider's firewall / security list
and close everything else there too (8069, 8070, 8072, 5432, 1433).

## Demo specifics — Cloudflare tunnel

Port 8070 is bound to 127.0.0.1 and never exposed. `cloudflared` opens an
**outbound** connection; no inbound port is needed.

```bash
./ops/server/harden_demo.sh --restart          # admin_passwd, list_db=False, proxy_mode, workers/limits
./ops/server/start_demo.sh                     # applies DEMO_ADMIN_PASSWORD from .env.demo
./ops/server/setup_cloudflare_tunnel.sh --service
./ops/server/setup_firewall.sh demo
```

The `trycloudflare.com` URL changes at every restart of the service; use a
named tunnel for anything shown to customers more than once.

## Backups

Plaintext backups stay on the host under `/opt/rubicon-backups` (root only).
Every off-site copy is encrypted with `age` before upload; the private key is
never on the server. Details: `ops/setup_oci_backup.md`, `ops/CRON.md`.

## Checklists

### Demo (run once)
- [ ] `./ops/server/harden_demo.sh --restart` executed
- [ ] `./ops/server/setup_cloudflare_tunnel.sh --service` active
- [ ] `./ops/server/setup_firewall.sh demo` active, provider firewall closes 8070
- [ ] `DEMO_ADMIN_PASSWORD` set in `.env.demo` (≠ `CHANGE_ME`)
- [ ] backup and healthcheck crons (`ops/CRON.md`)

### Production (before go-live)
- [ ] `./ops/server/harden_server.sh` and `./ops/server/setup_firewall.sh online` done; provider firewall mirrors 22/80/443
- [ ] `odoo_conf/odoo.prod.conf` with strong `admin_passwd`, `list_db = False`, no `logfile`
- [ ] `.env.prod` filled in (`chmod 600`), `BACKUP_AGE_RECIPIENT` set, `age` + oci CLI installed
- [ ] OCI bucket private, dedicated IAM user, lifecycle policy applied (`ops/setup_oci_backup.md`)
- [ ] `./ops/backup.sh prod` exits 0 and logs `uploaded prod/...`
- [ ] `./ops/verify_backup.sh prod` passes (automated restore test)
- [ ] backup + weekly restore-test crons configured (`ops/CRON.md`)
- [ ] `./ops/healthcheck.sh prod` passes without errors
- [ ] HTTPS answers, `http://<ip>:8069` does not
- [ ] administrator has 2FA; every person has a named account with a role group
- [ ] the age private key and a copy of `prod_config_*.tar.gz` are stored off-server (password manager)

## Secrets and sensitive files

Never committed (enforced by `.gitignore`):
- `.env` — development credentials
- `.env.demo` — demo credentials
- `.env.prod` — production credentials, API key, backup settings
- `.demo_secrets` — admin_passwd generated by harden_demo.sh
- `odoo_conf/odoo_demo.conf` — demo config with admin_passwd
- `odoo_conf/odoo.prod.conf` — production config with db_password and admin_passwd
- `/etc/wireguard/` — WireGuard keys (LAN variant, on the server only)

Also sensitive, outside the repository:
- `/opt/rubicon-backups/` — plaintext local backups (root only, `chmod 700`);
  the `*_config_*.tar.gz` archives contain `.env.prod` and `odoo.prod.conf`
- the `age` private key — never on the server; needed only to restore from OCI
- `/root/.oci/` — OCI API key of the dedicated backup user
- `mssql_backups/*.bak` — the pre-Odoo business data (`ops/migration/README.md`)
