#!/bin/bash
# Démarre le serveur demo et applique le mot de passe admin sécurisé.
# Usage: ./ops/start_demo.sh

set -e
SCRIPT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
ENV_FILE="$SCRIPT_DIR/.env.demo"
CONF_FILE="$SCRIPT_DIR/odoo_conf/odoo_demo.conf"
COMPOSE_FILE="$SCRIPT_DIR/docker-compose.demo.yml"

RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Charger les variables d'env
if [ ! -f "$ENV_FILE" ]; then
  echo "Erreur: $ENV_FILE introuvable"
  exit 1
fi
source "$ENV_FILE"

if [ -z "$DEMO_ADMIN_PASSWORD" ] || [ "$DEMO_ADMIN_PASSWORD" = "CHANGE_ME" ]; then
  echo -e "${RED}ERREUR SÉCURITÉ: DEMO_ADMIN_PASSWORD non défini ou CHANGE_ME dans .env.demo${NC}"
  echo "Définir un mot de passe fort avant de démarrer le serveur."
  exit 1
fi

# Vérifier que admin_passwd (database manager) est sécurisé dans odoo_demo.conf
if [ -f "$CONF_FILE" ]; then
  ADMIN_PASSWD_VAL=$(grep -E "^admin_passwd\s*=" "$CONF_FILE" 2>/dev/null | cut -d= -f2 | tr -d ' ' || echo "")
  if [ -z "$ADMIN_PASSWD_VAL" ] || [ "$ADMIN_PASSWD_VAL" = "CHANGE_ME" ]; then
    echo -e "${YELLOW}AVERTISSEMENT: admin_passwd non sécurisé dans odoo_demo.conf${NC}"
    echo "Exécuter d'abord: ./ops/harden_demo.sh --restart"
    echo ""
    read -p "Continuer quand même ? [y/N] " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
      echo "Annulé. Exécuter ./ops/harden_demo.sh pour sécuriser la configuration."
      exit 1
    fi
  fi
fi

echo "Démarrage du serveur demo..."
docker compose -f "$COMPOSE_FILE" up -d

echo "Attente que Odoo soit prêt..."
until docker compose -f "$COMPOSE_FILE" exec odoo_demo curl -s http://localhost:8069/web/health > /dev/null 2>&1; do
  sleep 3
done

echo "Application du mot de passe admin..."
docker compose -f "$COMPOSE_FILE" exec odoo_demo odoo shell -d rubicondemo --no-http <<EOF
env['res.users'].browse(2).write({'password': '$DEMO_ADMIN_PASSWORD'})
env.cr.commit()
print("Mot de passe admin mis à jour.")
EOF

echo ""
echo "Serveur demo prêt."
echo "  URL locale  : http://$(hostname -I | awk '{print $1}'):8070"
echo "  URL HTTPS   : voir 'sudo journalctl -u cloudflared-tunnel | grep trycloudflare'"
echo "  Login       : admin"
echo "  Password    : $DEMO_ADMIN_PASSWORD"
