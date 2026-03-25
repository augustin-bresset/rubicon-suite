#!/bin/bash
# Vérifie l'état de santé du serveur Rubicon.
# Usage: ./ops/healthcheck.sh [demo|prod]
# Retourne exit code 0 si tout OK, 1 si un problème est détecté.
# Compatible avec cron, Nagios, et UptimeRobot (via HTTP si exposé).

ENV="${1:-demo}"

SCRIPT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
PROBLEMS=()
WARNINGS=()

# ── Paramètres selon l'environnement ──────────────────────────────────────
if [ "$ENV" = "demo" ]; then
  COMPOSE_FILE="$SCRIPT_DIR/docker-compose.demo.yml"
  ODOO_SERVICE="odoo_demo"
  DB_SERVICE="db_demo"
  PORT=8070
  PREFIX="demo"
elif [ "$ENV" = "prod" ]; then
  COMPOSE_FILE="$SCRIPT_DIR/docker-compose.yml"
  ODOO_SERVICE="odoo"
  DB_SERVICE="db"
  PORT=8069
  PREFIX="prod"
else
  echo "Usage: $0 [demo|prod]"
  exit 1
fi

BACKUP_DIR="/opt/rubicon-backups"

# ── 1. Healthcheck HTTP Odoo ───────────────────────────────────────────────
if curl -sf "http://localhost:$PORT/web/health" > /dev/null 2>&1; then
  echo "✓ Odoo répond sur le port $PORT"
else
  PROBLEMS+=("Odoo ne répond pas sur http://localhost:$PORT/web/health")
fi

# ── 2. Container Odoo running ─────────────────────────────────────────────
if docker compose -f "$COMPOSE_FILE" ps "$ODOO_SERVICE" 2>/dev/null | grep -qiE "running|up"; then
  echo "✓ Container $ODOO_SERVICE en cours d'exécution"
else
  PROBLEMS+=("Container $ODOO_SERVICE n'est pas en état 'running'")
fi

# ── 3. Container DB running ───────────────────────────────────────────────
if docker compose -f "$COMPOSE_FILE" ps "$DB_SERVICE" 2>/dev/null | grep -qiE "running|up"; then
  echo "✓ Container $DB_SERVICE en cours d'exécution"
else
  PROBLEMS+=("Container $DB_SERVICE n'est pas en état 'running'")
fi

# ── 4. Espace disque ─────────────────────────────────────────────────────
DISK_USAGE=$(df / | tail -1 | awk '{print $5}' | tr -d '%')
if [ "$DISK_USAGE" -lt 80 ]; then
  echo "✓ Espace disque OK (${DISK_USAGE}% utilisé)"
elif [ "$DISK_USAGE" -lt 90 ]; then
  WARNINGS+=("Espace disque à ${DISK_USAGE}% — prévoir nettoyage")
else
  PROBLEMS+=("Espace disque critique : ${DISK_USAGE}% utilisé")
fi

# ── 5. Backup récent (< 25h) ──────────────────────────────────────────────
if [ -d "$BACKUP_DIR" ]; then
  RECENT_BACKUP=$(find "$BACKUP_DIR" -name "${PREFIX}_db_*.sql.gz" -mtime -1 2>/dev/null | head -1)
  if [ -n "$RECENT_BACKUP" ]; then
    echo "✓ Backup récent trouvé : $(basename "$RECENT_BACKUP")"
  else
    WARNINGS+=("Aucun backup DB trouvé dans les dernières 25h dans $BACKUP_DIR")
  fi
else
  WARNINGS+=("Répertoire backup $BACKUP_DIR inexistant")
fi

# ── 6. WireGuard (production seulement) ───────────────────────────────────
if [ "$ENV" = "prod" ]; then
  if ip link show wg0 &>/dev/null; then
    WG_PEERS=$(sudo wg show wg0 2>/dev/null | grep -c "^peer" || echo "0")
    echo "✓ WireGuard wg0 actif ($WG_PEERS peer(s))"
  else
    WARNINGS+=("Interface WireGuard wg0 inactive")
  fi
fi

# ── Résumé ─────────────────────────────────────────────────────────────────
echo ""

if [ ${#WARNINGS[@]} -gt 0 ]; then
  echo "⚠ AVERTISSEMENTS:"
  for w in "${WARNINGS[@]}"; do
    echo "  - $w"
  done
fi

if [ ${#PROBLEMS[@]} -gt 0 ]; then
  echo "✗ PROBLÈMES DÉTECTÉS:"
  for p in "${PROBLEMS[@]}"; do
    echo "  - $p"
  done
  exit 1
else
  echo "✓ Tous les contrôles OK (env: $ENV)"
  exit 0
fi
