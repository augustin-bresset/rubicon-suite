#!/bin/bash
# Restore the database and filestore from a backup.
# Usage: ./ops/restore.sh [demo|prod] <YYYYMMDD> [--from-oci]
#   demo         : restore rubicondemo
#   prod         : restore rubicon
#   YYYYMMDD     : backup date (e.g. 20260325)
#   --from-oci   : download from Oracle Object Storage first
#
# WARNING: destructive operation. The existing database will be replaced.

set -euo pipefail

ENV="${1:-}"
DATE_ARG="${2:-}"
FROM_OCI="${3:-}"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

if [ -z "$ENV" ] || [ -z "$DATE_ARG" ]; then
  echo "Usage: $0 [demo|prod] <YYYYMMDD> [--from-oci]"
  echo "Example: $0 prod 20260325"
  exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
BACKUP_DIR="/opt/rubicon-backups"
OCI_BUCKET="rubicon-backups"

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
  echo "Unknown environment: $ENV"
  exit 1
fi

DATE_DIR="$BACKUP_DIR/$DATE_ARG"

# ── Download from OCI if requested ────────────────────────────────────────
if [ "$FROM_OCI" = "--from-oci" ]; then
  if ! command -v oci &>/dev/null; then
    echo -e "${RED}oci CLI not installed. See ops/setup_oci_backup.md${NC}"
    exit 1
  fi
  echo "Downloading backups for $DATE_ARG from OCI..."
  mkdir -p "$DATE_DIR"

  # DB
  DB_OCI_KEY=$(oci os object list --bucket-name "$OCI_BUCKET" \
    --prefix "$ENV/$DATE_ARG/${PREFIX}_db_" \
    --query "data[0].name" --raw-output 2>/dev/null | tr -d '"' || echo "")
  if [ -z "$DB_OCI_KEY" ]; then
    echo -e "${RED}No DB backup found in OCI for $ENV/$DATE_ARG${NC}"
    exit 1
  fi
  oci os object get --bucket-name "$OCI_BUCKET" --name "$DB_OCI_KEY" \
    --file "$DATE_DIR/$(basename "$DB_OCI_KEY")"
  echo "DB downloaded: $(basename "$DB_OCI_KEY")"

  # Filestore
  FS_OCI_KEY=$(oci os object list --bucket-name "$OCI_BUCKET" \
    --prefix "$ENV/$DATE_ARG/${PREFIX}_filestore_" \
    --query "data[0].name" --raw-output 2>/dev/null | tr -d '"' || echo "")
  if [ -n "$FS_OCI_KEY" ]; then
    oci os object get --bucket-name "$OCI_BUCKET" --name "$FS_OCI_KEY" \
      --file "$DATE_DIR/$(basename "$FS_OCI_KEY")"
    echo "Filestore downloaded: $(basename "$FS_OCI_KEY")"
  fi
fi

# ── Find backup files ──────────────────────────────────────────────────────
DB_FILE=$(ls "$DATE_DIR/${PREFIX}_db_"*.sql.gz 2>/dev/null | sort | tail -1 || echo "")
FS_FILE=$(ls "$DATE_DIR/${PREFIX}_filestore_"*.tar.gz 2>/dev/null | sort | tail -1 || echo "")

if [ -z "$DB_FILE" ]; then
  echo -e "${RED}No DB backup found in $DATE_DIR/${NC}"
  echo "Available backups:"
  ls "$BACKUP_DIR"/ 2>/dev/null || echo "(no backups found)"
  exit 1
fi

echo ""
echo -e "${RED}=== RESTORE $ENV from $(basename "$DB_FILE") ===${NC}"
echo ""
echo "  DB backup   : $DB_FILE"
echo "  FS backup   : ${FS_FILE:-N/A}"
echo "  Target DB   : $DB_NAME"
echo ""
echo -e "${RED}WARNING: All current data in $DB_NAME will be DELETED.${NC}"
read -p "Confirm restore? [y/N] " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
  echo "Cancelled."
  exit 0
fi

# ── 1. Stop Odoo ───────────────────────────────────────────────────────────
echo "Stopping $ODOO_SERVICE..."
docker compose -f "$COMPOSE_FILE" stop "$ODOO_SERVICE" 2>/dev/null || true

# ── 2. Drop and recreate the database ─────────────────────────────────────
echo "Dropping database $DB_NAME..."
docker compose -f "$COMPOSE_FILE" exec -T "$DB_SERVICE" \
  psql -U "$DB_USER" -c "DROP DATABASE IF EXISTS $DB_NAME;" postgres

docker compose -f "$COMPOSE_FILE" exec -T "$DB_SERVICE" \
  psql -U "$DB_USER" -c "CREATE DATABASE $DB_NAME OWNER $DB_USER;" postgres

# ── 3. Restore the database ───────────────────────────────────────────────
echo "Restoring database from $(basename "$DB_FILE")..."
gunzip -c "$DB_FILE" | \
  docker compose -f "$COMPOSE_FILE" exec -T "$DB_SERVICE" \
    psql -U "$DB_USER" -d "$DB_NAME" -q

echo "Database restored."

# ── 4. Restore the filestore ──────────────────────────────────────────────
if [ -n "$FS_FILE" ]; then
  echo "Restoring filestore from $(basename "$FS_FILE")..."
  docker run --rm \
    -v "${VOLUME_NAME}:/data" \
    -v "$(dirname "$FS_FILE"):/backup:ro" \
    alpine \
    sh -c "rm -rf /data/* && tar xzf /backup/$(basename "$FS_FILE") -C /data"
  echo "Filestore restored."
else
  echo -e "${YELLOW}No filestore backup available — filestore not restored.${NC}"
fi

# ── 5. Restart Odoo ───────────────────────────────────────────────────────
echo "Starting $ODOO_SERVICE..."
docker compose -f "$COMPOSE_FILE" start "$ODOO_SERVICE"

# ── 6. Healthcheck ────────────────────────────────────────────────────────
echo "Waiting for healthcheck..."
PORT=$([ "$ENV" = "demo" ] && echo "8070" || echo "8069")
for i in $(seq 1 20); do
  if curl -sf "http://localhost:$PORT/web/health" > /dev/null 2>&1; then
    echo -e "${GREEN}Odoo responding on port $PORT.${NC}"
    break
  fi
  echo "  Waiting... ($i/20)"
  sleep 3
done

echo ""
echo -e "${GREEN}=== Restore $ENV complete ===${NC}"
