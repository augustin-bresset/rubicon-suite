#!/bin/bash
# Automated restore test: prove that the latest local backup can actually be
# restored. Meant for a weekly cron (ops/CRON.md); safe to run any time.
#
# Usage: ./ops/verify_backup.sh <dev|demo|prod>
#
# Steps:
#   1. ops/restore.sh <env> latest --target-db <db>_verify --neutralize --yes
#      (side restore: the live database and the running Odoo are untouched)
#   2. every table in VERIFY_TABLES must hold at least one row
#   3. if the database references filestore attachments, the restored
#      filestore must contain files
#   4. drop <db>_verify and its filestore
# On success $BACKUP_DIR/.last_verify_ok_<env> is touched; ops/healthcheck.sh
# warns when that marker is older than 8 days. Everything is appended to
# $BACKUP_DIR/verify.log. Exit code 0 only when every step passed.
#
# VERIFY_TABLES (space separated) overrides the default table list.

set -uo pipefail

ENV="${1:-}"
[ -n "$ENV" ] || { echo "Usage: $0 <dev|demo|prod>" >&2; exit 1; }

SCRIPT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
case "$ENV" in
  dev)  COMPOSE_FILE="$SCRIPT_DIR/docker-compose.yml";      ENV_FILE="$SCRIPT_DIR/.env";      DB_SERVICE="db";      ODOO_SERVICE="odoo";      FALLBACK_VOLUME="rubicon-suite_odoo_data" ;;
  demo) COMPOSE_FILE="$SCRIPT_DIR/docker-compose.demo.yml"; ENV_FILE="$SCRIPT_DIR/.env.demo"; DB_SERVICE="db_demo"; ODOO_SERVICE="odoo_demo"; FALLBACK_VOLUME="rubicon-suite_odoo_demo_data" ;;
  prod) COMPOSE_FILE="$SCRIPT_DIR/docker-compose.prod.yml"; ENV_FILE="$SCRIPT_DIR/.env.prod"; DB_SERVICE="db";      ODOO_SERVICE="odoo";      FALLBACK_VOLUME="rubicon-suite_prod_odoo_data" ;;
  *) echo "Usage: $0 <dev|demo|prod>" >&2; exit 1 ;;
esac
[ -f "$ENV_FILE" ] || { echo "Error: $ENV_FILE not found" >&2; exit 1; }
# shellcheck disable=SC1090
source "$ENV_FILE"
DB_NAME="${POSTGRES_DB:-${DB_NAME:-rubicon}}"
DB_USER="${POSTGRES_USER:-${DB_USER:-odoo}}"
BACKUP_DIR="${BACKUP_DIR:-/opt/rubicon-backups}"
VERIFY_DB="${VERIFY_DB:-${DB_NAME}_verify}"
VERIFY_TABLES="${VERIFY_TABLES:-res_users res_partner pdp_product_model pdp_product ir_attachment}"
LOG="$BACKUP_DIR/verify.log"
MARKER="$BACKUP_DIR/.last_verify_ok_${ENV}"
mkdir -p "$BACKUP_DIR"

compose() { docker compose -f "$COMPOSE_FILE" "$@"; }
count() { compose exec -T "$DB_SERVICE" psql -Atq -U "$DB_USER" -d "$VERIFY_DB" -c "$1" 2>/dev/null; }

resolve_volume() {
  local cid
  cid=$(compose ps -a -q "$ODOO_SERVICE" 2>/dev/null | head -1)
  [ -n "$cid" ] || return 0
  docker inspect -f '{{range .Mounts}}{{if eq .Destination "/var/lib/odoo/.local/share/Odoo"}}{{.Name}}{{end}}{{end}}' "$cid" 2>/dev/null || true
}

cleanup() {
  echo "Cleaning up: dropping $VERIFY_DB and its filestore"
  compose exec -T "$DB_SERVICE" psql -q -U "$DB_USER" -d postgres \
    -c "DROP DATABASE IF EXISTS \"$VERIFY_DB\" WITH (FORCE);" >/dev/null 2>&1 || echo "  (could not drop $VERIFY_DB)"
  local vol
  vol=$(resolve_volume); vol="${vol:-$FALLBACK_VOLUME}"
  docker run --rm -v "${vol}:/data" alpine:3 rm -rf "/data/filestore/$VERIFY_DB" >/dev/null 2>&1 || true
}

main() {
  local t n attachments files rc=0
  echo "=== Restore test $ENV — $(date '+%Y-%m-%d %H:%M:%S') ==="
  [ "$VERIFY_DB" != "$DB_NAME" ] || { echo "FAIL: VERIFY_DB must differ from the live database"; return 1; }

  if ! "$SCRIPT_DIR/ops/restore.sh" "$ENV" latest --target-db "$VERIFY_DB" --neutralize --yes; then
    echo "FAIL: restore.sh failed"
    cleanup
    return 1
  fi

  for t in $VERIFY_TABLES; do
    n=$(count "SELECT count(*) FROM $t") || n=""
    if [ -z "$n" ]; then echo "FAIL: table $t missing in restored database"; rc=1
    elif [ "$n" -eq 0 ]; then echo "FAIL: table $t is empty"; rc=1
    else echo "  ok  $t: $n rows"; fi
  done

  attachments=$(count "SELECT count(*) FROM ir_attachment WHERE store_fname IS NOT NULL") || attachments=0
  if [ "${attachments:-0}" -gt 0 ]; then
    local vol
    vol=$(resolve_volume); vol="${vol:-$FALLBACK_VOLUME}"
    files=$(docker run --rm -v "${vol}:/data:ro" alpine:3 sh -c "find /data/filestore/$VERIFY_DB -type f 2>/dev/null | wc -l" || echo 0)
    if [ "${files:-0}" -gt 0 ]; then echo "  ok  filestore: $files files for $attachments stored attachments"
    else echo "FAIL: $attachments attachments reference the filestore but no file was restored"; rc=1; fi
  fi

  neutralized=$(count "SELECT lower(value) FROM ir_config_parameter WHERE key = 'database.is_neutralized'") || neutralized=""
  if [ "$neutralized" = "true" ]; then echo "  ok  database is neutralized"
  else echo "FAIL: database not marked neutralized (value: '${neutralized:-none}')"; rc=1; fi

  cleanup
  if [ "$rc" -eq 0 ]; then
    touch "$MARKER"
    echo "=== RESTORE TEST OK ($ENV) ==="
  else
    echo "=== RESTORE TEST FAILED ($ENV) ==="
  fi
  return "$rc"
}

main 2>&1 | tee -a "$LOG"
exit "${PIPESTATUS[0]}"
