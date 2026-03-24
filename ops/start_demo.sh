#!/bin/bash
# Démarre le serveur demo et applique le mot de passe admin sécurisé.
# Usage: ./ops/start_demo.sh

set -e
SCRIPT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
ENV_FILE="$SCRIPT_DIR/.env.demo"
COMPOSE_FILE="$SCRIPT_DIR/docker-compose.demo.yml"

# Charger les variables d'env
if [ ! -f "$ENV_FILE" ]; then
  echo "Erreur: $ENV_FILE introuvable"
  exit 1
fi
source "$ENV_FILE"

if [ -z "$DEMO_ADMIN_PASSWORD" ]; then
  echo "Erreur: DEMO_ADMIN_PASSWORD non défini dans .env.demo"
  exit 1
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
echo "  URL     : http://$(hostname -I | awk '{print $1}'):8070"
echo "  Login   : admin"
echo "  Password: $DEMO_ADMIN_PASSWORD"
