#!/bin/bash
# Restore the database and filestore from a backup made by ops/backup.sh.
#
# Usage: ./ops/restore.sh <dev|demo|prod> <YYYYMMDD|latest> [options]
#   --from-oci          download the encrypted off-site copy first (prod)
#   --identity FILE     age private key for --from-oci (default: $BACKUP_AGE_IDENTITY)
#   --target-db NAME    restore into NAME instead of the stack's own database.
#                       Odoo keeps running on the live database; the filestore
#                       is restored under filestore/NAME. This is how restore
#                       tests (ops/verify_backup.sh) and inspections of old
#                       backups are done.
#   --neutralize        run `odoo neutralize` on the restored database: crons
#                       and outgoing mail servers disabled. Mandatory for any
#                       copy of production that is not production itself.
#   --yes               no interactive confirmation (cron / scripts)
#
# Restoring into the stack's own database is DESTRUCTIVE: Odoo is stopped, the
# database dropped and recreated, the whole data volume replaced.
#
# Integrity: SHA256SUMS is verified when present; the SQL restore runs with
# ON_ERROR_STOP so a partial restore cannot pass silently; the database is
# created like Odoo does (template0, LC_COLLATE 'C'); a row-count report is
# printed at the end.

set -euo pipefail

usage() {
  cat >&2 <<USAGE
Usage: $0 <dev|demo|prod> <YYYYMMDD|latest> [--from-oci] [--identity FILE] [--target-db NAME] [--neutralize] [--yes]
Examples:
  $0 prod 20260325                      # full restore of that day's backup
  $0 prod latest --target-db rubicon_verify --neutralize --yes
  $0 prod latest --from-oci --identity /root/.config/rubicon/backup.key
USAGE
  exit 1
}

ENV="${1:-}"
DATE_ARG="${2:-}"
[ -n "$ENV" ] && [ -n "$DATE_ARG" ] || usage
shift 2

# shellcheck source=lib/common.sh
source "$(dirname "$0")/lib/common.sh"
rubicon_env "$ENV"

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'
die() { echo -e "${RED}ERROR: $*${NC}" >&2; exit 1; }

# ── Options ────────────────────────────────────────────────────────────────
FROM_OCI=0; IDENTITY="${BACKUP_AGE_IDENTITY:-}"; TARGET_DB=""; NEUTRALIZE=0; YES=0
while [ $# -gt 0 ]; do
  case "$1" in
    --from-oci)   FROM_OCI=1 ;;
    --identity)   IDENTITY="${2:-}"; shift ;;
    --target-db)  TARGET_DB="${2:-}"; shift ;;
    --neutralize) NEUTRALIZE=1 ;;
    --yes|-y)     YES=1 ;;
    *) usage ;;
  esac
  shift
done
TARGET_DB="${TARGET_DB:-$DB_NAME}"
[[ "$TARGET_DB" =~ ^[A-Za-z0-9_]+$ ]] || die "invalid database name: $TARGET_DB"
SIDE_RESTORE=0
[ "$TARGET_DB" = "$DB_NAME" ] || SIDE_RESTORE=1

psql_admin() { compose exec -T "$DB_SERVICE" psql -v ON_ERROR_STOP=1 -q -U "$DB_USER" -d postgres "$@"; }
running "$DB_SERVICE" || die "container $DB_SERVICE is not running (start the stack first)"

# ── Off-site helpers ───────────────────────────────────────────────────────
oci_list() {
  oci os object list --bucket-name "$OCI_BUCKET" --prefix "$1" --all \
    --query 'data[].name' --raw-output 2>/dev/null \
  | python3 -c 'import json,sys
t = sys.stdin.read().strip()
d = json.loads(t) if t and t != "null" else []
[print(n) for n in (d if isinstance(d, list) else [])]'
}
oci_latest_date() {
  oci_list "$ENV/" | grep -E "/${PREFIX}_db_[0-9_]+\.sql\.gz(\.age)?$" \
    | sed -E 's#^.*/([0-9]{8})/[^/]+$#\1#' | sort -u | tail -1
}
oci_download() {
  local keys key name
  mapfile -t keys < <(oci_list "$ENV/" | grep -E "^$ENV/((daily|weekly|monthly)/)?$DATE_ARG/")
  [ ${#keys[@]} -gt 0 ] || die "no off-site backup for $ENV/$DATE_ARG in bucket $OCI_BUCKET"
  mkdir -p "$DATE_DIR"
  for key in "${keys[@]}"; do
    name=$(basename "$key")
    echo "  downloading $key"
    oci os object get --bucket-name "$OCI_BUCKET" --name "$key" --file "$DATE_DIR/$name" >/dev/null \
      || die "download of $key failed"
    if [[ "$name" == *.age ]]; then
      [ -n "$IDENTITY" ] && [ -f "$IDENTITY" ] \
        || die "encrypted backup: pass --identity <age private key file> (or set BACKUP_AGE_IDENTITY)"
      command -v age >/dev/null 2>&1 || die "age is required to decrypt (apt install age)"
      age -d -i "$IDENTITY" -o "$DATE_DIR/${name%.age}" "$DATE_DIR/$name" || die "decryption of $name failed"
      rm -f "$DATE_DIR/$name"
    fi
  done
}
local_latest_date() {
  local dir
  for dir in $(ls -d "$BACKUP_DIR"/[0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9] 2>/dev/null | sort -r); do
    if ls "$dir/${PREFIX}_db_"*.sql.gz >/dev/null 2>&1; then basename "$dir"; return 0; fi
  done
  return 1
}

# ── Locate the backup ──────────────────────────────────────────────────────
if [ "$FROM_OCI" = 1 ]; then
  command -v oci >/dev/null 2>&1 || die "oci CLI not installed (ops/setup_oci_backup.md)"
  [ -n "$OCI_BUCKET" ] || die "OCI_BUCKET is empty in $ENV_FILE"
  if [ "$DATE_ARG" = "latest" ]; then
    DATE_ARG=$(oci_latest_date)
    [ -n "$DATE_ARG" ] || die "no off-site backup found under $ENV/ in bucket $OCI_BUCKET"
  fi
  DATE_DIR="$BACKUP_DIR/$DATE_ARG"
  echo "Downloading off-site backup $ENV/$DATE_ARG..."
  oci_download
else
  if [ "$DATE_ARG" = "latest" ]; then
    DATE_ARG=$(local_latest_date) || die "no local $PREFIX backup found in $BACKUP_DIR"
  fi
  DATE_DIR="$BACKUP_DIR/$DATE_ARG"
fi
[[ "$DATE_ARG" =~ ^[0-9]{8}$ ]] || die "invalid date: $DATE_ARG (expected YYYYMMDD or latest)"

DB_FILE=$(ls "$DATE_DIR/${PREFIX}_db_"*.sql.gz 2>/dev/null | sort | tail -1 || true)
if [ -z "$DB_FILE" ]; then
  echo -e "${RED}No DB backup found in $DATE_DIR/${NC}" >&2
  echo "Available local backups:" >&2
  ls "$BACKUP_DIR" 2>/dev/null >&2 || echo "(none)" >&2
  exit 1
fi
# Pair the filestore archive with the DB dump of the same run (same timestamp);
# fall back to the latest one of the day.
STAMP=$(basename "$DB_FILE" .sql.gz); STAMP="${STAMP#${PREFIX}_db_}"
FS_FILE="$DATE_DIR/${PREFIX}_filestore_${STAMP}.tar.gz"
[ -f "$FS_FILE" ] || FS_FILE=$(ls "$DATE_DIR/${PREFIX}_filestore_"*.tar.gz 2>/dev/null | sort | tail -1 || true)

# ── Integrity ──────────────────────────────────────────────────────────────
if [ -f "$DATE_DIR/SHA256SUMS" ]; then
  echo "Verifying checksums..."
  (cd "$DATE_DIR" && sha256sum -c --ignore-missing --quiet SHA256SUMS) \
    || die "checksum verification FAILED — backup files are corrupt or were tampered with"
  echo "  checksums OK"
else
  echo -e "${YELLOW}WARNING: no SHA256SUMS in $DATE_DIR — integrity not verified (backup made by an older backup.sh)${NC}"
fi
gzip -t "$DB_FILE" || die "DB archive is corrupt (gzip -t)"
[ -z "$FS_FILE" ] || tar tzf "$FS_FILE" >/dev/null || die "filestore archive is corrupt (tar -t)"

# ── Confirmation ───────────────────────────────────────────────────────────
echo ""
echo -e "${RED}=== RESTORE $ENV: $(basename "$DB_FILE") -> database '$TARGET_DB' ===${NC}"
echo "  DB backup    : $DB_FILE"
echo "  FS backup    : ${FS_FILE:-N/A}"
echo "  Neutralize   : $([ "$NEUTRALIZE" = 1 ] && echo yes || echo no)"
if [ "$SIDE_RESTORE" = 1 ]; then
  echo "  Mode         : side restore (live database '$DB_NAME' and running Odoo untouched)"
else
  echo -e "  Mode         : ${RED}FULL — Odoo stopped, database '$DB_NAME' and its filestore REPLACED${NC}"
fi
echo ""
if [ "$YES" = 0 ]; then
  read -r -p "Confirm restore? [y/N] " REPLY
  [[ $REPLY =~ ^[Yy]$ ]] || { echo "Cancelled."; exit 0; }
fi

# ── Data volume ────────────────────────────────────────────────────────────
VOLUME_NAME=$(resolve_volume)
docker volume inspect "$VOLUME_NAME" >/dev/null 2>&1 || die "Docker volume $VOLUME_NAME not found"

# ── 1. Stop Odoo (full restore only) ───────────────────────────────────────
if [ "$SIDE_RESTORE" = 0 ]; then
  echo "Stopping $ODOO_SERVICE..."
  compose stop "$ODOO_SERVICE"
fi

# ── 2. Recreate the database (same settings as Odoo's own create) ──────────
echo "Recreating database $TARGET_DB..."
psql_admin -c "DROP DATABASE IF EXISTS \"$TARGET_DB\" WITH (FORCE);"
psql_admin -c "CREATE DATABASE \"$TARGET_DB\" OWNER \"$DB_USER\" ENCODING 'unicode' LC_COLLATE 'C' TEMPLATE template0;"

# ── 3. Load the dump ───────────────────────────────────────────────────────
echo "Restoring $(basename "$DB_FILE") into $TARGET_DB (this can take a while)..."
gunzip -c "$DB_FILE" \
  | compose exec -T "$DB_SERVICE" psql -v ON_ERROR_STOP=1 -q -U "$DB_USER" -d "$TARGET_DB" >/dev/null \
  || die "SQL restore failed — database $TARGET_DB is incomplete"
echo "  database restored"

# ── 4. Filestore ───────────────────────────────────────────────────────────
if [ -n "$FS_FILE" ]; then
  FS_NAME=$(basename "$FS_FILE")
  if [ "$SIDE_RESTORE" = 0 ]; then
    echo "Restoring data volume $VOLUME_NAME from $FS_NAME..."
    docker run --rm -v "${VOLUME_NAME}:/data" -v "$DATE_DIR:/backup:ro" alpine:3 sh -c \
      "find /data -mindepth 1 -delete && tar xzf /backup/$FS_NAME -C /data" \
      || die "filestore restore failed"
  else
    echo "Restoring filestore/$DB_NAME from $FS_NAME as filestore/$TARGET_DB..."
    docker run --rm -v "${VOLUME_NAME}:/data" -v "$DATE_DIR:/backup:ro" alpine:3 sh -c "
      set -e
      rm -rf /data/filestore/$TARGET_DB /data/.restore_tmp
      mkdir -p /data/.restore_tmp /data/filestore
      tar xzf /backup/$FS_NAME -C /data/.restore_tmp ./filestore/$DB_NAME 2>/dev/null || true
      if [ -d /data/.restore_tmp/filestore/$DB_NAME ]; then
        mv /data/.restore_tmp/filestore/$DB_NAME /data/filestore/$TARGET_DB
      else
        echo '  (archive holds no filestore/$DB_NAME — empty filestore)'
      fi
      rm -rf /data/.restore_tmp" \
      || die "filestore restore failed"
  fi
  echo "  filestore restored"
else
  echo -e "${YELLOW}No filestore archive for this backup — filestore not restored.${NC}"
fi

# ── 5. Start Odoo (full restore only) ──────────────────────────────────────
if [ "$SIDE_RESTORE" = 0 ]; then
  echo "Starting $ODOO_SERVICE..."
  compose up -d "$ODOO_SERVICE"
fi

# ── 6. Neutralize ──────────────────────────────────────────────────────────
if [ "$NEUTRALIZE" = 1 ]; then
  echo "Neutralizing $TARGET_DB (crons and outgoing mail disabled)..."
  odoo_cli neutralize -d "$TARGET_DB" >/dev/null || die "odoo neutralize failed"
  echo "  neutralized"
fi

# ── 7. Report ──────────────────────────────────────────────────────────────
echo "Row counts in $TARGET_DB:"
for t in res_users res_partner pdp_product_model pdp_product pdp_product_stone sis_document sis_document_item ir_attachment; do
  n=$(compose exec -T "$DB_SERVICE" psql -Atq -U "$DB_USER" -d "$TARGET_DB" -c "SELECT count(*) FROM $t" 2>/dev/null || echo "n/a")
  printf "  %-22s %s\n" "$t" "$n"
done
FS_COUNT=$(docker run --rm -v "${VOLUME_NAME}:/data:ro" alpine:3 sh -c "find /data/filestore/$TARGET_DB -type f 2>/dev/null | wc -l" || echo "?")
printf "  %-22s %s\n" "filestore files" "$FS_COUNT"

if [ "$SIDE_RESTORE" = 0 ]; then
  echo "Waiting for Odoo on port $PORT..."
  for i in $(seq 1 30); do
    if curl -sf "http://localhost:$PORT/web/health" >/dev/null 2>&1; then
      echo -e "${GREEN}Odoo responding on port $PORT.${NC}"
      break
    fi
    [ "$i" -lt 30 ] || echo -e "${YELLOW}Odoo not responding yet — check: docker compose -f $COMPOSE_FILE logs $ODOO_SERVICE${NC}"
    sleep 3
  done
fi

echo ""
echo -e "${GREEN}=== Restore $ENV -> $TARGET_DB complete ===${NC}"
