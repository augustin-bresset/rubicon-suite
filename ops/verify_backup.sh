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

# shellcheck source=lib/common.sh
source "$(dirname "$0")/lib/common.sh"
rubicon_env "$ENV"
VERIFY_DB="${VERIFY_DB:-${DB_NAME}_verify}"
VERIFY_TABLES="${VERIFY_TABLES:-res_users res_partner pdp_product_model pdp_product ir_attachment}"
LOG="$BACKUP_DIR/verify.log"
MARKER="$BACKUP_DIR/.last_verify_ok_${ENV}"
mkdir -p "$BACKUP_DIR"

count() { compose exec -T "$DB_SERVICE" psql -Atq -U "$DB_USER" -d "$VERIFY_DB" -c "$1" 2>/dev/null; }

cleanup() {
  echo "Cleaning up: dropping $VERIFY_DB and its filestore"
  compose exec -T "$DB_SERVICE" psql -q -U "$DB_USER" -d postgres \
    -c "DROP DATABASE IF EXISTS \"$VERIFY_DB\" WITH (FORCE);" >/dev/null 2>&1 || echo "  (could not drop $VERIFY_DB)"
  local vol
  vol=$(resolve_volume)
  docker run --rm -v "${vol}:/data" alpine:3 rm -rf "/data/filestore/$VERIFY_DB" >/dev/null 2>&1 || true
}

main() {
  local t n attachments files rc=0
  echo "=== Restore test $ENV — $(date '+%Y-%m-%d %H:%M:%S') ==="
  [ "$VERIFY_DB" != "$DB_NAME" ] || { echo "FAIL: VERIFY_DB must differ from the live database"; return 1; }

  if ! "$REPO_DIR/ops/restore.sh" "$ENV" latest --target-db "$VERIFY_DB" --neutralize --yes; then
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
    vol=$(resolve_volume)
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
