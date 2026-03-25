#!/bin/bash
# Start the demo server and apply the secure admin password.
# Usage: ./ops/start_demo.sh

set -e
SCRIPT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
ENV_FILE="$SCRIPT_DIR/.env.demo"
CONF_FILE="$SCRIPT_DIR/odoo_conf/odoo_demo.conf"
COMPOSE_FILE="$SCRIPT_DIR/docker-compose.demo.yml"

RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Load environment variables
if [ ! -f "$ENV_FILE" ]; then
  echo "Error: $ENV_FILE not found"
  exit 1
fi
source "$ENV_FILE"

if [ -z "$DEMO_ADMIN_PASSWORD" ] || [ "$DEMO_ADMIN_PASSWORD" = "CHANGE_ME" ]; then
  echo -e "${RED}SECURITY ERROR: DEMO_ADMIN_PASSWORD not set or is CHANGE_ME in .env.demo${NC}"
  echo "Set a strong password before starting the server."
  exit 1
fi

# Verify that admin_passwd (database manager) is secured in odoo_demo.conf
if [ -f "$CONF_FILE" ]; then
  ADMIN_PASSWD_VAL=$(grep -E "^admin_passwd\s*=" "$CONF_FILE" 2>/dev/null | cut -d= -f2 | tr -d ' ' || echo "")
  if [ -z "$ADMIN_PASSWD_VAL" ] || [ "$ADMIN_PASSWD_VAL" = "CHANGE_ME" ]; then
    echo -e "${YELLOW}WARNING: admin_passwd not secured in odoo_demo.conf${NC}"
    echo "Run first: ./ops/harden_demo.sh --restart"
    echo ""
    read -p "Continue anyway? [y/N] " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
      echo "Cancelled. Run ./ops/harden_demo.sh to secure the configuration."
      exit 1
    fi
  fi
fi

echo "Starting demo server..."
docker compose -f "$COMPOSE_FILE" up -d

echo "Waiting for Odoo to be ready..."
until docker compose -f "$COMPOSE_FILE" exec odoo_demo curl -s http://localhost:8069/web/health > /dev/null 2>&1; do
  sleep 3
done

echo "Applying admin password..."
docker compose -f "$COMPOSE_FILE" exec odoo_demo odoo shell -d rubicondemo --no-http <<EOF
env['res.users'].browse(2).write({'password': '$DEMO_ADMIN_PASSWORD'})
env.cr.commit()
print("Admin password updated.")
EOF

echo ""
echo "Demo server ready."
echo "  Local URL   : http://$(hostname -I | awk '{print $1}'):8070"
echo "  HTTPS URL   : see 'sudo journalctl -u cloudflared-tunnel | grep trycloudflare'"
echo "  Login       : admin"
echo "  Password    : $DEMO_ADMIN_PASSWORD"
