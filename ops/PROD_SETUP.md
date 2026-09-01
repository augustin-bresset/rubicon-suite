# Production setup — Internet-facing server

Ordered procedure to bring Rubicon Suite online on a public VPS. Every step
is a script or a documented command; nothing here is meant to be improvised.

## 0. Sizing and prerequisites

- Ubuntu 24.04 LTS (or Debian 12), 2 vCPU, 4 GB RAM, 40 GB SSD. The Odoo
  container is limited to 4 GiB in `docker-compose.prod.yml`; go to 8 GB RAM
  and `workers = 4` if more than ~10 concurrent users.
- A DNS `A` record for the domain (e.g. `erp.rubicon.co.th`) pointing at the
  server, unless you use a named Cloudflare tunnel.
- Your SSH public key installed for a non-root user with sudo.
- Off-site pieces prepared on a workstation: the `age` key pair
  (`ops/setup_oci_backup.md` §5) and the OCI bucket (§1–2, §6).

## 1. Harden the host

```bash
git clone <repo-url> /opt/rubicon && cd /opt/rubicon
./ops/server/harden_server.sh            # SSH key-only, fail2ban, unattended-upgrades, age
./ops/server/setup_firewall.sh online    # 22 (SSH_ALLOW_FROM=<cidr> to restrict), 80, 443
```

Mirror 22/80/443 in the provider's firewall (Oracle security list, Hetzner
firewall, ...). Test a fresh SSH login before closing the current session.

## 2. Docker

```bash
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker "$USER" && newgrp docker
docker compose version
```

## 3. Configuration and secrets

```bash
cp .env.prod.example .env.prod && chmod 600 .env.prod
cp odoo_conf/odoo.conf.prod.example odoo_conf/odoo.prod.conf && chmod 600 odoo_conf/odoo.prod.conf
```

Fill in `.env.prod` (`POSTGRES_*`, `API_KEY_METAL_MARKET`,
`BACKUP_AGE_RECIPIENT`, `OCI_BUCKET`) and `odoo.prod.conf` (`db_user`,
`db_password`, `admin_passwd`). `ops/init_prod.sh` refuses to run while a
`CHANGE_ME` remains.

## 4. Database

Either a fresh database:

```bash
./ops/init_prod.sh                       # installs the modules without demo data, asks for the admin password
```

or a restore of an existing one (dev/demo export made with `ops/backup.sh`,
copied to `/opt/rubicon-backups/<YYYYMMDD>/`):

```bash
docker compose -f docker-compose.prod.yml up -d db
./ops/restore.sh prod <YYYYMMDD>
```

or, last resort, the rebuild from the legacy `.bak` files: `ops/migration/README.md`.

## 5. Reverse proxy and TLS

With a domain:

```bash
sudo apt install -y nginx certbot python3-certbot-nginx
sed "s/YOUR_DOMAIN/erp.example.com/g" ops/server/nginx_prod.conf | sudo tee /etc/nginx/sites-available/rubicon >/dev/null
sudo ln -sf /etc/nginx/sites-available/rubicon /etc/nginx/sites-enabled/rubicon
sudo rm -f /etc/nginx/sites-enabled/default
sudo certbot --nginx -d erp.example.com
sudo nginx -t && sudo systemctl reload nginx
./ops/server/harden_server.sh            # re-run: enables the nginx-limit-req fail2ban jail
```

Without a domain: a **named** Cloudflare tunnel (not `trycloudflare`, whose
URL changes at every restart) with two ingress rules — `/websocket` →
`http://127.0.0.1:8072`, everything else → `http://127.0.0.1:8069` — and a
Cloudflare Access policy in front of it.

Check: `curl -sI https://erp.example.com/web/login | head -1` → `HTTP/2 200`;
`curl -s --max-time 5 http://<server-ip>:8069/` → no answer.

## 6. Backups and monitoring

```bash
./ops/backup.sh prod                     # first backup; must end with "uploaded prod/..."
./ops/verify_backup.sh prod              # first restore test
./ops/healthcheck.sh prod
sudo crontab -e                          # paste the production block of ops/CRON.md
```

Store off-server: the `age` private key, `.env.prod`, `odoo.prod.conf` (also
inside every `prod_config_*.tar.gz` backup).

## 7. Users

1. Log in as the administrator, enable two-factor authentication
   (Preferences › Account Security).
2. Create one named user per person; give them the Rubicon access groups
   (`ops/SECURITY.md` › Access control) — never share the administrator account.
3. Disable the accounts of people who leave; they keep their history.

## 8. Updating the code

```bash
cd /opt/rubicon && ./ops/backup.sh prod          # always before an upgrade
git pull
docker compose -f docker-compose.prod.yml exec -T odoo odoo -d rubicon -u pdp_frontend,sis_frontend,rubicon_uom --stop-after-init
docker compose -f docker-compose.prod.yml restart odoo
./ops/healthcheck.sh prod
```

Image upgrades (Odoo or PostgreSQL patch releases): bump the digest in
`docker-compose.prod.yml`, then `docker compose -f docker-compose.prod.yml pull && ... up -d`.
A PostgreSQL major upgrade is a `ops/backup.sh` → new volume → `ops/restore.sh`.

## Go-live checklist

- [ ] `harden_server.sh` and `setup_firewall.sh online` done; provider firewall mirrors 22/80/443
- [ ] `.env.prod` and `odoo.prod.conf` without `CHANGE_ME`, mode 600
- [ ] `docker compose -f docker-compose.prod.yml ps` shows both services healthy
- [ ] HTTPS answers; `http://<ip>:8069` does not
- [ ] `ops/backup.sh prod` uploaded an encrypted copy; `ops/verify_backup.sh prod` passed
- [ ] crons installed (`sudo crontab -l`)
- [ ] administrator has 2FA; every person has a named account with the right groups
- [ ] `age` private key + config archive stored off-server
