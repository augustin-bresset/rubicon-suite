#!/bin/bash
# Backup de la base de données et du filestore Odoo.
# Usage: ./ops/backup.sh [demo|prod] [--no-oci]
#   demo     : sauvegarde rubicondemo (local seulement)
#   prod     : sauvegarde rubicon (local + Oracle Object Storage)
#   --no-oci : désactive l'upload OCI même pour prod
#
# Prérequis:
#   - Docker Compose stack démarrée
#   - Pour prod avec OCI: oci CLI configuré (voir ops/setup_oci_backup.md)

set -euo pipefail

ENV="${1:-demo}"
NO_OCI="${2:-}"

# ── Configuration ──────────────────────────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
BACKUP_DIR="/opt/rubicon-backups"
LOG_FILE="/var/log/rubicon-backup.log"
RETENTION_LOCAL_DAYS=7
RETENTION_OCI_DAYS=30
OCI_BUCKET="rubicon-backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
DATE_DIR=$(date +%Y%m%d)

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# ── Paramètres selon l'environnement ──────────────────────────────────────
if [ "$ENV" = "demo" ]; then
  COMPOSE_FILE="$SCRIPT_DIR/docker-compose.demo.yml"
  DB_SERVICE="db_demo"
  ODOO_SERVICE="odoo_demo"
  DB_NAME="rubicondemo"
  DB_USER="odoo"
  VOLUME_NAME="rubicon-suite_odoo_demo_data"
  PREFIX="demo"
elif [ "$ENV" = "prod" ]; then
  COMPOSE_FILE="$SCRIPT_DIR/docker-compose.yml"
  DB_SERVICE="db"
  ODOO_SERVICE="odoo"
  # Charger DB_NAME depuis .env si disponible
  if [ -f "$SCRIPT_DIR/.env" ]; then
    source "$SCRIPT_DIR/.env"
    DB_NAME="${DB_NAME:-rubicon}"
    DB_USER="${DB_USER:-rubicondev}"
  else
    DB_NAME="rubicon"
    DB_USER="rubicondev"
  fi
  VOLUME_NAME="rubicon-suite_odoo_data"
  PREFIX="prod"
else
  echo "Usage: $0 [demo|prod] [--no-oci]"
  exit 1
fi

# ── Initialisation ────────────────────────────────────────────────────────
mkdir -p "$BACKUP_DIR/$DATE_DIR"
exec >> "$LOG_FILE" 2>&1 || true  # Log si possible (non-fatal si /var/log non accessible)

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*"; }
fail() { echo -e "${RED}[$(date '+%Y-%m-%d %H:%M:%S')] ERREUR: $*${NC}"; exit 1; }

log "=== Début backup $ENV ($TIMESTAMP) ==="

# ── 1. Vérifier que les containers tournent ───────────────────────────────
if ! docker compose -f "$COMPOSE_FILE" ps "$DB_SERVICE" 2>/dev/null | grep -q "running\|Up"; then
  fail "Le container $DB_SERVICE n'est pas en cours d'exécution. Démarrer la stack d'abord."
fi

# ── 2. Backup de la base de données ──────────────────────────────────────
DB_FILE="$BACKUP_DIR/$DATE_DIR/${PREFIX}_db_${TIMESTAMP}.sql.gz"
log "Backup DB $DB_NAME → $DB_FILE"

docker compose -f "$COMPOSE_FILE" exec -T "$DB_SERVICE" \
  pg_dump -U "$DB_USER" "$DB_NAME" | gzip > "$DB_FILE" \
  || fail "pg_dump échoué"

DB_SIZE=$(du -sh "$DB_FILE" | cut -f1)
log "DB backup OK — taille: $DB_SIZE"

# ── 3. Backup du filestore (volume Docker) ────────────────────────────────
FILESTORE_FILE="$BACKUP_DIR/$DATE_DIR/${PREFIX}_filestore_${TIMESTAMP}.tar.gz"
log "Backup filestore (volume $VOLUME_NAME) → $FILESTORE_FILE"

# Utilise un container Alpine temporaire pour accéder au volume
docker run --rm \
  -v "${VOLUME_NAME}:/data:ro" \
  -v "$BACKUP_DIR/$DATE_DIR:/backup" \
  alpine \
  tar czf "/backup/${PREFIX}_filestore_${TIMESTAMP}.tar.gz" -C /data . \
  || fail "Backup filestore échoué"

FS_SIZE=$(du -sh "$FILESTORE_FILE" | cut -f1)
log "Filestore backup OK — taille: $FS_SIZE"

# ── 4. Upload vers Oracle Object Storage (prod uniquement) ─────────────────
if [ "$ENV" = "prod" ] && [ "$NO_OCI" != "--no-oci" ]; then
  if ! command -v oci &>/dev/null; then
    log "AVERTISSEMENT: oci CLI non installé — upload OCI ignoré. Voir ops/setup_oci_backup.md"
  else
    log "Upload vers Oracle Object Storage (bucket: $OCI_BUCKET)..."

    oci os object put \
      --bucket-name "$OCI_BUCKET" \
      --file "$DB_FILE" \
      --name "$ENV/$DATE_DIR/${PREFIX}_db_${TIMESTAMP}.sql.gz" \
      --force \
      && log "Upload DB OCI OK" \
      || log "AVERTISSEMENT: Upload DB OCI échoué (backup local conservé)"

    oci os object put \
      --bucket-name "$OCI_BUCKET" \
      --file "$FILESTORE_FILE" \
      --name "$ENV/$DATE_DIR/${PREFIX}_filestore_${TIMESTAMP}.tar.gz" \
      --force \
      && log "Upload filestore OCI OK" \
      || log "AVERTISSEMENT: Upload filestore OCI échoué (backup local conservé)"

    # Rotation OCI (supprimer objets > RETENTION_OCI_DAYS jours)
    CUTOFF_DATE=$(date -d "-${RETENTION_OCI_DAYS} days" +%Y%m%d 2>/dev/null || \
                  date -v-${RETENTION_OCI_DAYS}d +%Y%m%d 2>/dev/null || echo "")
    if [ -n "$CUTOFF_DATE" ]; then
      log "Nettoyage OCI : suppression objets antérieurs à $CUTOFF_DATE"
      oci os object list --bucket-name "$OCI_BUCKET" --prefix "$ENV/" \
        --query "data[?\"time-created\" < '${CUTOFF_DATE}'].name" \
        --raw-output 2>/dev/null | \
        tr -d '[]"' | tr ',' '\n' | \
        while read -r obj; do
          [ -n "$obj" ] && oci os object delete \
            --bucket-name "$OCI_BUCKET" --object-name "$obj" --force 2>/dev/null \
            && log "OCI supprimé: $obj" || true
        done
    fi
  fi
fi

# ── 5. Rotation locale ─────────────────────────────────────────────────────
log "Rotation locale (>$RETENTION_LOCAL_DAYS jours)..."
find "$BACKUP_DIR" -name "${PREFIX}_*.sql.gz" -mtime "+$RETENTION_LOCAL_DAYS" -delete 2>/dev/null || true
find "$BACKUP_DIR" -name "${PREFIX}_*.tar.gz" -mtime "+$RETENTION_LOCAL_DAYS" -delete 2>/dev/null || true
# Supprimer les répertoires de date vides
find "$BACKUP_DIR" -type d -empty -delete 2>/dev/null || true

# ── 6. Résumé ─────────────────────────────────────────────────────────────
TOTAL_LOCAL=$(du -sh "$BACKUP_DIR" 2>/dev/null | cut -f1 || echo "?")
log "=== Backup $ENV terminé — stockage local total: $TOTAL_LOCAL ==="
echo -e "${GREEN}Backup $ENV terminé avec succès.${NC}"
echo "  DB        : $DB_FILE ($DB_SIZE)"
echo "  Filestore : $FILESTORE_FILE ($FS_SIZE)"
echo "  Log       : $LOG_FILE"
