#!/bin/bash
# Rubicon Demo — Setup script
# Run once to initialize the demo environment (local or VPS)
# Usage: bash demo_setup.sh

set -e

echo "=== Rubicon Demo Setup ==="
echo ""

# --- 1. Generate passwords ---
DB_PASS=$(python3 -c "import secrets; print(secrets.token_urlsafe(16))")
MASTER_PASS=$(python3 -c "import secrets; print(secrets.token_hex(24))")

# --- 2. Create .env.demo ---
cat > .env.demo << EOF
POSTGRES_DB=rubicondemo
POSTGRES_USER=odoo
POSTGRES_PASSWORD=${DB_PASS}
EOF
echo "✓ .env.demo created"

# --- 3. Create odoo_conf/odoo_demo.conf ---
cat > odoo_conf/odoo_demo.conf << EOF
[options]
addons_path = /mnt/extra-addons,/mnt/external-addons/oca_currency,/usr/lib/python3/dist-packages/odoo/addons
db_host = db_demo
db_port = 5432
db_user = odoo
db_password = ${DB_PASS}

http_interface = 0.0.0.0

dbfilter = ^rubicondemo$
without_demo = False

; Protects /web/database/manager — do not share
admin_passwd = ${MASTER_PASS}
EOF
echo "✓ odoo_conf/odoo_demo.conf created"

# --- 4. Start the stack ---
echo ""
echo "Starting demo stack..."
docker compose -f docker-compose.demo.yml down -v 2>/dev/null || true
docker compose -f docker-compose.demo.yml up -d

echo ""
echo "Waiting for database to be ready..."
sleep 8

# --- 5. Initialize Odoo database ---
echo "Installing modules (this takes ~2 minutes)..."
docker compose -f docker-compose.demo.yml exec odoo_demo odoo \
  -d rubicondemo \
  -i rubicon_demo,pdp_frontend,sis_frontend,rubicon_uom,metal_price \
  --stop-after-init

# --- 6. Restart in normal mode ---
docker compose -f docker-compose.demo.yml up -d

echo ""
echo "========================================"
echo "  Demo ready at http://localhost:8070"
echo "  Login:    admin"
echo "  Password: admin  ← change this after first login!"
echo ""
echo "  DB master password (for /web/database/manager):"
echo "  ${MASTER_PASS}"
echo "========================================"
echo ""
echo "IMPORTANT: Change the Odoo admin password after first login."
echo "  Settings → Users → Administrator → Change Password"
