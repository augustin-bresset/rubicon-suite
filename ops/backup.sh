#!/bin/bash
# Backup the Odoo database, filestore and stack configuration.
#
# Usage: ./ops/backup.sh <dev|demo|prod> [--no-oci]
#   dev      : local development stack (docker-compose.yml)
#   demo     : rubicondemo (local only)
#   prod     : rubicon (local + encrypted off-site copy on Oracle Object Storage)
#   --no-oci : skip the off-site upload even for prod
#
# Output, under $BACKUP_DIR/YYYYMMDD/ (BACKUP_DIR: /opt/rubicon-backups, overridable
# from the env file or the environment):
#   <env>_db_<ts>.sql.gz          pg_dump, plain SQL (--no-owner), gzip
#   <env>_filestore_<ts>.tar.gz   Odoo data volume (filestore + sessions)
#   <env>_config_<ts>.tar.gz      env file + odoo conf (mode 600). Without them a
#                                 restore on a new host is impossible.
#   SHA256SUMS                    checksums of the files above (checked by restore.sh)
# Every archive is integrity-checked (gzip -t / tar -t) and must exceed a
# minimum size before the run is reported OK.
#
# Off-site (prod only, unless --no-oci or OCI_BUCKET is empty): each file is
# encrypted with `age` to BACKUP_AGE_RECIPIENT and uploaded as
#   <env>/<tier>/<YYYYMMDD>/<file>.age
# where tier = monthly (1st of the month), weekly (Sunday) or daily. Retention
# on OCI is a bucket lifecycle policy per tier (ops/setup_oci_backup.md), not
# this script. Plaintext never leaves the host.
#
# Local retention (grandfather-father-son):
#   daily 7 days, Sunday backups 35 days, 1st-of-month backups 400 days.
#
# Exit codes: 0 OK, 1 backup failed (nothing usable produced), 2 local backup
# OK but a non-fatal step (off-site copy, config archive) reported a problem.
# $BACKUP_DIR/.last_status_<env> records the outcome for ops/healthcheck.sh.
# The full log goes to $LOG_FILE (default $BACKUP_DIR/backup.log); only a
# one-line summary is printed to stdout, so cron mail stays readable.
#
# Prerequisites: docker compose stack running. For prod off-site copies:
# `age` (apt install age) and the oci CLI configured (ops/setup_oci_backup.md).

set -euo pipefail

ENV="${1:-}"
NO_OCI="${2:-}"

usage() { echo "Usage: $0 <dev|demo|prod> [--no-oci]" >&2; exit 1; }
[ -n "$ENV" ] || usage
[ -z "$NO_OCI" ] || [ "$NO_OCI" = "--no-oci" ] || usage

# shellcheck source=lib/common.sh
source "$(dirname "$0")/lib/common.sh"
rubicon_env "$ENV"

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
DATE_DIR=$(date +%Y%m%d)

RETENTION_DAILY_DAYS="${RETENTION_DAILY_DAYS:-7}"
RETENTION_WEEKLY_DAYS="${RETENTION_WEEKLY_DAYS:-35}"
RETENTION_MONTHLY_DAYS="${RETENTION_MONTHLY_DAYS:-400}"
MIN_DB_BYTES="${MIN_DB_BYTES:-200000}"           # a real dump is many MB; an empty DB is ~50 KB
MIN_FILESTORE_BYTES="${MIN_FILESTORE_BYTES:-1024}"
LOG_FILE="${LOG_FILE:-$BACKUP_DIR/backup.log}"

OUT_DIR="$BACKUP_DIR/$DATE_DIR"
mkdir -p "$OUT_DIR"
chmod 700 "$BACKUP_DIR" 2>/dev/null || true

# ── Logging: everything to $LOG_FILE, one summary line to the caller ───────
exec 3>&1
if touch "$LOG_FILE" 2>/dev/null; then
  exec >>"$LOG_FILE" 2>&1
else
  echo "WARNING: cannot write $LOG_FILE, logging to stdout" >&3
fi

STATUS_FILE="$BACKUP_DIR/.last_status_${PREFIX}"
WARNINGS=0
log()  { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*"; }
warn() { log "WARNING: $*"; WARNINGS=$((WARNINGS + 1)); }
fail() {
  log "ERROR: $*"
  echo "FAIL $(date '+%Y-%m-%dT%H:%M:%S') $*" > "$STATUS_FILE"
  echo "Backup $ENV FAILED: $* (log: $LOG_FILE)" >&3
  exit 1
}

log "=== Starting backup $ENV ($TIMESTAMP) — db=$DB_NAME out=$OUT_DIR ==="

# ── 1. Stack must be running; locate the Odoo data volume ─────────────────
running "$DB_SERVICE" || fail "container $DB_SERVICE is not running (start the stack first)"
VOLUME_NAME=$(resolve_volume)
docker volume inspect "$VOLUME_NAME" >/dev/null 2>&1 || fail "Docker volume $VOLUME_NAME not found"

# ── 2. Database ────────────────────────────────────────────────────────────
DB_FILE="$OUT_DIR/${PREFIX}_db_${TIMESTAMP}.sql.gz"
log "Dumping database $DB_NAME -> $DB_FILE"
compose exec -T "$DB_SERVICE" pg_dump -U "$DB_USER" --no-owner --no-privileges "$DB_NAME" \
  | gzip -c > "$DB_FILE" || fail "pg_dump failed"
gzip -t "$DB_FILE" || fail "DB archive is corrupt (gzip -t)"
DB_BYTES=$(stat -c %s "$DB_FILE")
[ "$DB_BYTES" -ge "$MIN_DB_BYTES" ] || fail "DB archive suspiciously small ($DB_BYTES bytes < $MIN_DB_BYTES)"
log "DB OK — $(du -h "$DB_FILE" | cut -f1)"

# ── 3. Filestore (Docker volume) ───────────────────────────────────────────
FS_FILE="$OUT_DIR/${PREFIX}_filestore_${TIMESTAMP}.tar.gz"
log "Archiving volume $VOLUME_NAME -> $FS_FILE"
docker run --rm -v "${VOLUME_NAME}:/data:ro" -v "$OUT_DIR:/backup" alpine:3 \
  tar czf "/backup/$(basename "$FS_FILE")" -C /data . \
  || fail "filestore archive failed"
tar tzf "$FS_FILE" >/dev/null || fail "filestore archive is corrupt (tar -t)"
FS_BYTES=$(stat -c %s "$FS_FILE")
[ "$FS_BYTES" -ge "$MIN_FILESTORE_BYTES" ] || fail "filestore archive suspiciously small ($FS_BYTES bytes)"
log "Filestore OK — $(du -h "$FS_FILE" | cut -f1)"

# ── 4. Stack configuration (env file + odoo conf) ──────────────────────────
FILES=("$DB_FILE" "$FS_FILE")
CONFIG_FILE="$OUT_DIR/${PREFIX}_config_${TIMESTAMP}.tar.gz"
present=()
for f in "${CONFIG_FILES[@]}"; do
  if [ -f "$REPO_DIR/$f" ]; then present+=("$f"); else warn "config file $f not found, not archived"; fi
done
if [ ${#present[@]} -gt 0 ]; then
  (umask 077 && tar czf "$CONFIG_FILE" -C "$REPO_DIR" "${present[@]}") || fail "config archive failed"
  chmod 600 "$CONFIG_FILE"
  FILES+=("$CONFIG_FILE")
  log "Config OK — ${present[*]}"
fi

# ── 5. Checksums ───────────────────────────────────────────────────────────
names=()
for f in "${FILES[@]}"; do names+=("$(basename "$f")"); done
(cd "$OUT_DIR" && sha256sum "${names[@]}") >> "$OUT_DIR/SHA256SUMS"
log "Checksums appended to $OUT_DIR/SHA256SUMS"

# ── 6. Off-site copy (prod): encrypt, upload ───────────────────────────────
TIER=daily
[ "$(date +%u)" = "7" ] && TIER=weekly
[ "$(date +%d)" = "01" ] && TIER=monthly

if [ "$ENV" = "prod" ] && [ "$NO_OCI" != "--no-oci" ] && [ -n "$OCI_BUCKET" ]; then
  if ! command -v oci >/dev/null 2>&1; then
    warn "oci CLI not installed — off-site copy skipped (ops/setup_oci_backup.md)"
  elif ! command -v age >/dev/null 2>&1; then
    warn "age not installed (apt install age) — off-site copy skipped: plaintext never leaves the host"
  elif [ -z "$BACKUP_AGE_RECIPIENT" ]; then
    warn "BACKUP_AGE_RECIPIENT is empty in .env.prod — off-site copy skipped: plaintext never leaves the host"
  else
    log "Encrypting and uploading to OCI bucket $OCI_BUCKET (tier: $TIER)"
    ENC_DIR=$(mktemp -d)
    trap 'rm -rf "$ENC_DIR"' EXIT
    for f in "${FILES[@]}"; do
      name=$(basename "$f")
      if age -r "$BACKUP_AGE_RECIPIENT" -o "$ENC_DIR/$name.age" "$f"; then
        if oci os object put --bucket-name "$OCI_BUCKET" --file "$ENC_DIR/$name.age" \
             --name "$ENV/$TIER/$DATE_DIR/$name.age" --force >/dev/null; then
          log "  uploaded $ENV/$TIER/$DATE_DIR/$name.age"
        else
          warn "upload of $name.age failed (local copy retained)"
        fi
        rm -f "$ENC_DIR/$name.age"
      else
        warn "encryption of $name failed — not uploaded"
      fi
    done
    oci os object put --bucket-name "$OCI_BUCKET" --file "$OUT_DIR/SHA256SUMS" \
      --name "$ENV/$TIER/$DATE_DIR/SHA256SUMS" --force >/dev/null \
      || warn "upload of SHA256SUMS failed"
  fi
elif [ "$ENV" = "prod" ]; then
  log "Off-site copy disabled (--no-oci or empty OCI_BUCKET)"
fi

# ── 7. Local rotation (GFS) ────────────────────────────────────────────────
log "Local rotation: daily>${RETENTION_DAILY_DAYS}d, Sunday>${RETENTION_WEEKLY_DAYS}d, 1st-of-month>${RETENTION_MONTHLY_DAYS}d"
NOW=$(date +%s)
for dir in "$BACKUP_DIR"/[0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9]; do
  [ -d "$dir" ] || continue
  d=$(basename "$dir")
  ts=$(date -d "$d" +%s 2>/dev/null) || continue
  age_days=$(( (NOW - ts) / 86400 ))
  keep_days=$RETENTION_DAILY_DAYS
  [ "$(date -d "$d" +%u)" = "7" ] && keep_days=$RETENTION_WEEKLY_DAYS
  [ "${d:6:2}" = "01" ] && keep_days=$RETENTION_MONTHLY_DAYS
  [ "$age_days" -gt "$keep_days" ] || continue
  removed=0
  for f in "$dir/${PREFIX}_"*; do
    [ -e "$f" ] || continue
    rm -f "$f"; removed=$((removed + 1))
  done
  [ "$removed" -eq 0 ] || log "  removed $removed file(s) from $d (age ${age_days}d > ${keep_days}d)"
  # Drop the directory once no backup of any environment is left in it
  if ! ls "$dir"/*_db_* >/dev/null 2>&1 && ! ls "$dir"/*_filestore_* >/dev/null 2>&1; then
    rm -f "$dir/SHA256SUMS"
    rmdir "$dir" 2>/dev/null || true
  fi
done

# ── 8. Summary ─────────────────────────────────────────────────────────────
TOTAL_LOCAL=$(du -sh "$BACKUP_DIR" 2>/dev/null | cut -f1 || echo "?")
SUMMARY="db $(du -h "$DB_FILE" | cut -f1), filestore $(du -h "$FS_FILE" | cut -f1) -> $OUT_DIR (local total $TOTAL_LOCAL)"
if [ "$WARNINGS" -gt 0 ]; then
  echo "WARN $(date '+%Y-%m-%dT%H:%M:%S') $WARNINGS warning(s), see $LOG_FILE" > "$STATUS_FILE"
  log "=== Backup $ENV finished with $WARNINGS warning(s) ==="
  echo "Backup $ENV OK locally with $WARNINGS warning(s) (log: $LOG_FILE): $SUMMARY" >&3
  exit 2
fi
echo "OK $(date '+%Y-%m-%dT%H:%M:%S') $(basename "$DB_FILE")" > "$STATUS_FILE"
log "=== Backup $ENV complete ==="
echo "Backup $ENV OK: $SUMMARY" >&3
