#!/bin/bash
# Backup the Odoo database and filestore.
# Usage: ./ops/backup.sh [demo|prod] [--no-oci]
#   demo     : backup rubicondemo (local only)
#   prod     : backup rubicon (local + Oracle Object Storage)
#   --no-oci : disable OCI upload even for prod
#
# Prerequisites:
#   - Docker Compose stack running
#   - For prod with OCI: oci CLI configured (see ops/setup_oci_backup.md)

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

# ── Environment parameters ─────────────────────────────────────────────────
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
  # Load DB_NAME from .env if available
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

# ── Initialization ─────────────────────────────────────────────────────────
mkdir -p "$BACKUP_DIR/$DATE_DIR"
exec >> "$LOG_FILE" 2>&1 || true  # Log if possible (non-fatal if /var/log not writable)

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*"; }
fail() { echo -e "${RED}[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: $*${NC}"; exit 1; }

log "=== Starting backup $ENV ($TIMESTAMP) ==="

# ── 1. Check containers are running ───────────────────────────────────────
if ! docker compose -f "$COMPOSE_FILE" ps "$DB_SERVICE" 2>/dev/null | grep -q "running\|Up"; then
  fail "Container $DB_SERVICE is not running. Start the stack first."
fi

# ── 2. Database backup ─────────────────────────────────────────────────────
DB_FILE="$BACKUP_DIR/$DATE_DIR/${PREFIX}_db_${TIMESTAMP}.sql.gz"
log "Backing up DB $DB_NAME → $DB_FILE"

docker compose -f "$COMPOSE_FILE" exec -T "$DB_SERVICE" \
  pg_dump -U "$DB_USER" "$DB_NAME" | gzip > "$DB_FILE" \
  || fail "pg_dump failed"

DB_SIZE=$(du -sh "$DB_FILE" | cut -f1)
log "DB backup OK — size: $DB_SIZE"

# ── 3. Filestore backup (Docker volume) ───────────────────────────────────
FILESTORE_FILE="$BACKUP_DIR/$DATE_DIR/${PREFIX}_filestore_${TIMESTAMP}.tar.gz"
log "Backing up filestore (volume $VOLUME_NAME) → $FILESTORE_FILE"

# Use a temporary Alpine container to access the volume
docker run --rm \
  -v "${VOLUME_NAME}:/data:ro" \
  -v "$BACKUP_DIR/$DATE_DIR:/backup" \
  alpine \
  tar czf "/backup/${PREFIX}_filestore_${TIMESTAMP}.tar.gz" -C /data . \
  || fail "Filestore backup failed"

FS_SIZE=$(du -sh "$FILESTORE_FILE" | cut -f1)
log "Filestore backup OK — size: $FS_SIZE"

# ── 4. Upload to Oracle Object Storage (prod only) ─────────────────────────
if [ "$ENV" = "prod" ] && [ "$NO_OCI" != "--no-oci" ]; then
  if ! command -v oci &>/dev/null; then
    log "WARNING: oci CLI not installed — OCI upload skipped. See ops/setup_oci_backup.md"
  else
    log "Uploading to Oracle Object Storage (bucket: $OCI_BUCKET)..."

    oci os object put \
      --bucket-name "$OCI_BUCKET" \
      --file "$DB_FILE" \
      --name "$ENV/$DATE_DIR/${PREFIX}_db_${TIMESTAMP}.sql.gz" \
      --force \
      && log "OCI DB upload OK" \
      || log "WARNING: OCI DB upload failed (local backup retained)"

    oci os object put \
      --bucket-name "$OCI_BUCKET" \
      --file "$FILESTORE_FILE" \
      --name "$ENV/$DATE_DIR/${PREFIX}_filestore_${TIMESTAMP}.tar.gz" \
      --force \
      && log "OCI filestore upload OK" \
      || log "WARNING: OCI filestore upload failed (local backup retained)"

    # OCI rotation (delete objects older than RETENTION_OCI_DAYS days)
    CUTOFF_DATE=$(date -d "-${RETENTION_OCI_DAYS} days" +%Y%m%d 2>/dev/null || \
                  date -v-${RETENTION_OCI_DAYS}d +%Y%m%d 2>/dev/null || echo "")
    if [ -n "$CUTOFF_DATE" ]; then
      log "OCI cleanup: deleting objects older than $CUTOFF_DATE"
      oci os object list --bucket-name "$OCI_BUCKET" --prefix "$ENV/" \
        --query "data[?\"time-created\" < '${CUTOFF_DATE}'].name" \
        --raw-output 2>/dev/null | \
        tr -d '[]"' | tr ',' '\n' | \
        while read -r obj; do
          [ -n "$obj" ] && oci os object delete \
            --bucket-name "$OCI_BUCKET" --object-name "$obj" --force 2>/dev/null \
            && log "OCI deleted: $obj" || true
        done
    fi
  fi
fi

# ── 5. Local rotation ──────────────────────────────────────────────────────
log "Local rotation (>$RETENTION_LOCAL_DAYS days)..."
find "$BACKUP_DIR" -name "${PREFIX}_*.sql.gz" -mtime "+$RETENTION_LOCAL_DAYS" -delete 2>/dev/null || true
find "$BACKUP_DIR" -name "${PREFIX}_*.tar.gz" -mtime "+$RETENTION_LOCAL_DAYS" -delete 2>/dev/null || true
# Remove empty date directories
find "$BACKUP_DIR" -type d -empty -delete 2>/dev/null || true

# ── 6. Summary ─────────────────────────────────────────────────────────────
TOTAL_LOCAL=$(du -sh "$BACKUP_DIR" 2>/dev/null | cut -f1 || echo "?")
log "=== Backup $ENV complete — total local storage: $TOTAL_LOCAL ==="
echo -e "${GREEN}Backup $ENV completed successfully.${NC}"
echo "  DB        : $DB_FILE ($DB_SIZE)"
echo "  Filestore : $FILESTORE_FILE ($FS_SIZE)"
echo "  Log       : $LOG_FILE"
