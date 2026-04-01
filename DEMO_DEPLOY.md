# Rubicon Demo — Deployment Guide

The demo runs as a separate Docker stack on port `8070`, using the database `rubicondemo`.
It shares the same codebase as production — no code is duplicated.

---

## Local demo (quick test on your dev machine)

```bash
# 1. Create credentials file (never committed)
cp .env.demo.example .env.demo
# Edit .env.demo — change DEMO_DB_PASS to anything

# 2. Set the Odoo master password in odoo_conf/odoo_demo.conf
#    Replace CHANGE_ME_BEFORE_GOING_ONLINE with a real value:
python3 -c "import secrets; print(secrets.token_hex(24))"
# Paste the output into admin_passwd = ...

# 3. Start the stack
docker compose -f docker-compose.demo.yml up -d

# 4. Fix filestore permissions (required after every fresh volume creation)
#    Docker creates volumes as root; Odoo needs to own them.
sleep 8
docker compose -f docker-compose.demo.yml exec --user root odoo_demo \
  chown -R odoo:odoo /var/lib/odoo

# 5. Initialize the database (first time only — takes ~3 minutes)
docker compose -f docker-compose.demo.yml exec odoo_demo odoo \
  -d rubicondemo \
  -i rubicon_demo,pdp_frontend,sis_frontend,rubicon_uom \
  --stop-after-init

# 6. Restart Odoo in normal mode
docker compose -f docker-compose.demo.yml up -d

# 6. Open http://localhost:8070
#    Login: admin / admin
```
If failing with a filestore error (e.g. FileNotFoundError), it means the filestore volume is in a bad state. To reset it, run:

```sh
docker compose -f docker-compose.demo.yml down -v
docker compose -f docker-compose.demo.yml up -d
                                       
docker compose -f docker-compose.demo.yml exec --user root odoo_demo chown -R odoo:odoo /var/lib/odoo

docker compose -f docker-compose.demo.yml exec odoo_demo odoo \
  -d rubicondemo -i rubicon_demo,pdp_frontend,sis_frontend,rubicon_uom \
  --stop-after-init

docker compose -f docker-compose.demo.yml up -d  

```

## VPS deployment (publicly accessible demo)

### Requirements

- Ubuntu 22.04 / Debian 12 VPS — minimum 2 vCPU, 2 GB RAM, 20 GB disk
- Docker + Docker Compose installed
- A domain name pointing to the VPS (or just use the IP)

### Steps

#### 1. Copy files to the server

```bash
# From your dev machine — copy only what the demo needs
rsync -av \
  rubicon_addons/ \
  external_addons/ \
  data/pictures/ \
  odoo_conf/odoo_demo.conf \
  docker-compose.demo.yml \
  .env.demo.example \
  user@YOUR_VPS_IP:/opt/rubicon-demo/
```

> Or clone the full repo and use the same directory layout.

#### 2. Set credentials on the server

```bash
ssh user@YOUR_VPS_IP
cd /opt/rubicon-demo

# Create .env.demo with strong passwords
cp .env.demo.example .env.demo
nano .env.demo
# Set DEMO_DB_PASS to a strong random value

# Set Odoo master password
python3 -c "import secrets; print(secrets.token_hex(24))"
nano odoo_conf/odoo_demo.conf
# Replace CHANGE_ME_BEFORE_GOING_ONLINE with the generated value
```

#### 3. Initialize and start

```bash
docker compose -f docker-compose.demo.yml up -d
docker compose -f docker-compose.demo.yml exec odoo_demo odoo \
  -d rubicondemo \
  -i rubicon_demo,pdp_frontend,sis_frontend,rubicon_uom \
  --stop-after-init
docker compose -f docker-compose.demo.yml up -d

```

The demo is now running on `http://YOUR_VPS_IP:8070`.
* http://89.168.58.215:8070

#### 4. HTTPS with nginx + Let's Encrypt (required for a real public demo)

```bash
apt install nginx certbot python3-certbot-nginx

# Get SSL certificate (replace demo.yourdomain.com)
certbot --nginx -d demo.yourdomain.com
```

Create `/etc/nginx/sites-available/rubicon-demo`:

```nginx
server {
    listen 80;
    server_name demo.yourdomain.com;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl;
    server_name demo.yourdomain.com;

    ssl_certificate     /etc/letsencrypt/live/demo.yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/demo.yourdomain.com/privkey.pem;

    # Required for Odoo long-polling
    proxy_read_timeout 720s;
    proxy_connect_timeout 720s;
    proxy_send_timeout 720s;

    location / {
        proxy_pass http://127.0.0.1:8070;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

```bash
ln -s /etc/nginx/sites-available/rubicon-demo /etc/nginx/sites-enabled/
nginx -t && systemctl reload nginx
```

The demo is now at `https://demo.yourdomain.com`.

---

## Securing the admin account

After the first login (`admin` / `admin`), immediately:

1. Go to **Settings → Users → Administrator**
2. Change the password to something strong
3. Optionally rename the user to a less obvious name

If the demo is public, consider restricting who can log in:
- Create a read-only demo user (`demo` / `demo123`) with limited menus
- Or add HTTP Basic Auth at the nginx level so only invited people can access it

---

## Resetting the demo data

To wipe and re-initialize the database from scratch:

```bash
# Drop and recreate
docker compose -f docker-compose.demo.yml exec odoo_demo odoo \
  -d rubicondemo --drop-db 2>/dev/null; \
docker compose -f docker-compose.demo.yml exec odoo_demo odoo \
  -d rubicondemo \
  -i rubicon_demo,pdp_frontend,sis_frontend,rubicon_uom,metal_price \
  --stop-after-init

docker compose -f docker-compose.demo.yml up -d
```

---

## Stopping the demo

```bash
docker compose -f docker-compose.demo.yml down
# To also delete all data:
docker compose -f docker-compose.demo.yml down -v
```
