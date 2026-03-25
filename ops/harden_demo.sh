#!/bin/bash
# Durcit la configuration de sécurité du serveur demo.
# Usage: ./ops/harden_demo.sh [--restart]
#   --restart : redémarre odoo_demo après la mise à jour
#
# Ce script :
#   1. Génère un admin_passwd fort et l'applique dans odoo_demo.conf
#   2. Active list_db=False, proxy_mode=True, workers, limits
#   3. Vérifie que .env.demo contient DEMO_ADMIN_PASSWORD sécurisé

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
CONF_FILE="$SCRIPT_DIR/odoo_conf/odoo_demo.conf"
ENV_FILE="$SCRIPT_DIR/.env.demo"
COMPOSE_FILE="$SCRIPT_DIR/docker-compose.demo.yml"
RESTART="${1:-}"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# ── Vérifications préalables ───────────────────────────────────────────────
if [ ! -f "$CONF_FILE" ]; then
  echo -e "${RED}Erreur: $CONF_FILE introuvable.${NC}"
  echo "Créer ce fichier depuis odoo_conf/odoo_demo.conf.example avant de continuer."
  exit 1
fi

if [ ! -f "$ENV_FILE" ]; then
  echo -e "${RED}Erreur: $ENV_FILE introuvable.${NC}"
  echo "Créer ce fichier depuis .env.demo.example avant de continuer."
  exit 1
fi

source "$ENV_FILE"

if [ -z "$DEMO_ADMIN_PASSWORD" ] || [ "$DEMO_ADMIN_PASSWORD" = "CHANGE_ME" ]; then
  echo -e "${RED}ERREUR SÉCURITÉ: DEMO_ADMIN_PASSWORD non défini ou CHANGE_ME dans .env.demo${NC}"
  echo "Définir un mot de passe fort avant de continuer."
  exit 1
fi

echo -e "${GREEN}=== Durcissement de la configuration demo ===${NC}"
echo ""

# ── Générer admin_passwd fort ─────────────────────────────────────────────
ADMIN_PASSWD=$(python3 -c "import secrets; print(secrets.token_hex(24))")
echo -e "${YELLOW}admin_passwd généré (48 chars hex).${NC}"
echo "Ce mot de passe protège /web/database/manager."

# ── Appliquer les paramètres dans odoo_demo.conf ──────────────────────────
# Fonction : ajoute ou remplace une option dans le fichier .conf
set_conf() {
  local key="$1"
  local value="$2"
  if grep -q "^${key}\s*=" "$CONF_FILE" 2>/dev/null; then
    sed -i "s|^${key}\s*=.*|${key} = ${value}|" "$CONF_FILE"
  else
    echo "${key} = ${value}" >> "$CONF_FILE"
  fi
}

echo ""
echo "Application des paramètres de sécurité..."

set_conf "admin_passwd"       "$ADMIN_PASSWD"
set_conf "list_db"            "False"
set_conf "proxy_mode"         "True"
set_conf "workers"            "2"
set_conf "max_cron_threads"   "1"
set_conf "limit_time_cpu"     "60"
set_conf "limit_time_real"    "120"
set_conf "limit_memory_hard"  "2684354560"

echo ""
echo -e "${GREEN}Paramètres appliqués dans $CONF_FILE :${NC}"
echo "  admin_passwd       = [48 chars, non affiché]"
echo "  list_db            = False"
echo "  proxy_mode         = True"
echo "  workers            = 2"
echo "  max_cron_threads   = 1"
echo "  limit_time_cpu     = 60"
echo "  limit_time_real    = 120"
echo "  limit_memory_hard  = 2684354560 (2.5 GB)"

# ── Sauvegarder admin_passwd dans un fichier local sécurisé ───────────────
SECRETS_FILE="$SCRIPT_DIR/.demo_secrets"
echo "# Généré par harden_demo.sh — NE PAS COMMITER" > "$SECRETS_FILE"
echo "DEMO_DB_MANAGER_PASSWORD=$ADMIN_PASSWD" >> "$SECRETS_FILE"
chmod 600 "$SECRETS_FILE"
echo ""
echo -e "${YELLOW}admin_passwd sauvegardé dans .demo_secrets (chmod 600, gitignored).${NC}"

# ── S'assurer que .demo_secrets est gitignored ────────────────────────────
GITIGNORE="$SCRIPT_DIR/.gitignore"
if ! grep -q "\.demo_secrets" "$GITIGNORE" 2>/dev/null; then
  echo ".demo_secrets" >> "$GITIGNORE"
fi

# ── Redémarrer si demandé ─────────────────────────────────────────────────
if [ "$RESTART" = "--restart" ]; then
  echo ""
  echo "Redémarrage de odoo_demo..."
  docker compose -f "$COMPOSE_FILE" restart odoo_demo
  echo -e "${GREEN}odoo_demo redémarré.${NC}"
fi

echo ""
echo -e "${GREEN}=== Durcissement terminé ===${NC}"
echo ""
echo "Prochaines étapes :"
echo "  1. Vérifier que le tunnel Cloudflare est actif"
echo "  2. Configurer le firewall : ./ops/setup_firewall.sh"
echo "  3. Tester : curl http://localhost:8070/web/health"
if [ "$RESTART" != "--restart" ]; then
  echo "  4. Redémarrer odoo_demo :"
  echo "     docker compose -f docker-compose.demo.yml restart odoo_demo"
fi
