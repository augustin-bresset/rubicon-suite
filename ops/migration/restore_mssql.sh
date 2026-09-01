#!/bin/bash
# Restore the legacy SQL Server backups (.bak) into a throw-away SQL Server
# container and export their tables to CSV for rubicon_import/raw_to_data.
#
# Usage: ops/migration/restore_mssql.sh <pdp|sis|pictures|all> [--keep]
#   pdp       JMS-PDP21*.bak -> data/backup_pdp/<Table>.csv   (every base table)
#   sis       JMS-SIS21*.bak -> data/backup_sis/<Table>.csv   (every base table)
#   pictures  Pictures.bak   -> data/pictures/*.jpg + manifest.csv
#                              (through export/export_pictures_products.py)
#   --keep    leave the SQL Server container running for inspection; the SA
#             password is printed at the end
#
# Environment:
#   BAK_DIR            directory holding the .bak files   (default: mssql_backups)
#   EXPORT_ROOT        where backup_pdp/, backup_sis/, pictures/ are written (default: data)
#   MSSQL_SA_PASSWORD  SA password of the container       (default: random per run)
#   MSSQL_IMAGE        default mcr.microsoft.com/mssql/server:2019-latest
#
# The container listens on 127.0.0.1:1433 only. When $BAK_DIR/SHA256SUMS
# exists the .bak files are verified against it first (create it once, on the
# machine that received the files: `sha256sum *.bak > SHA256SUMS`).
# CSV format is bcp's `-c -t,` output: no header, comma separated, char
# columns padded to their width, CR LF inside text fields kept as stored
# (the converters re-join split rows), NUL bytes stripped. Two legacy tables are misspelled in
# SQL Server (StoneCatagories, ProductCatagories); their CSVs are renamed to
# the spelling the converters use.

set -euo pipefail

WHAT="${1:-}"
KEEP="${2:-}"
usage() { echo "Usage: $0 <pdp|sis|pictures|all> [--keep]" >&2; exit 1; }
case "$WHAT" in pdp|sis|pictures|all) ;; *) usage ;; esac
[ -z "$KEEP" ] || [ "$KEEP" = "--keep" ] || usage

REPO_DIR="$(cd "$(dirname "$0")/../.." && pwd)"
BAK_DIR="${BAK_DIR:-$REPO_DIR/mssql_backups}"
BAK_DIR="$(cd "$BAK_DIR" && pwd)"
EXPORT_ROOT="${EXPORT_ROOT:-$REPO_DIR/data}"
MSSQL_IMAGE="${MSSQL_IMAGE:-mcr.microsoft.com/mssql/server:2019-latest}"
CONTAINER="rubicon_mssql"
TOOLS="/opt/mssql-tools18/bin"

die() { echo "ERROR: $*" >&2; exit 1; }
log() { echo "[$(date '+%H:%M:%S')] $*"; }

# ── Backup files ───────────────────────────────────────────────────────────
find_bak() {  # find_bak <glob> -> newest matching file name (basename)
  local f
  f=$(ls -1 "$BAK_DIR"/$1 2>/dev/null | sort | tail -1 || true)
  [ -n "$f" ] || die "no $1 in $BAK_DIR"
  basename "$f"
}
if [ -f "$BAK_DIR/SHA256SUMS" ]; then
  log "Verifying .bak checksums against $BAK_DIR/SHA256SUMS"
  (cd "$BAK_DIR" && sha256sum -c --ignore-missing --quiet SHA256SUMS) || die ".bak checksum mismatch — the backup files are damaged"
else
  log "No $BAK_DIR/SHA256SUMS — .bak integrity not verified (create it with: cd $BAK_DIR && sha256sum *.bak > SHA256SUMS)"
fi

# ── SQL Server container ───────────────────────────────────────────────────
if docker ps -a --format '{{.Names}}' | grep -qx "$CONTAINER"; then
  if docker ps --format '{{.Names}}' | grep -qx "$CONTAINER"; then
    [ -n "${MSSQL_SA_PASSWORD:-}" ] || die "$CONTAINER is already running: pass MSSQL_SA_PASSWORD, or remove it with 'docker rm -f $CONTAINER'"
    log "Reusing running container $CONTAINER"
  else
    docker rm -f "$CONTAINER" >/dev/null
  fi
fi
SA_PW="${MSSQL_SA_PASSWORD:-$(python3 -c 'import secrets; print("Ms1!" + secrets.token_urlsafe(18))')}"
mkdir -p "$EXPORT_ROOT/backup_pdp" "$EXPORT_ROOT/backup_sis" "$EXPORT_ROOT/pictures"
EXPORT_ROOT="$(cd "$EXPORT_ROOT" && pwd)"
if ! docker ps --format '{{.Names}}' | grep -qx "$CONTAINER"; then
  log "Starting $MSSQL_IMAGE as $CONTAINER (127.0.0.1:1433)"
  docker run -d --name "$CONTAINER" \
    -e ACCEPT_EULA=Y -e MSSQL_SA_PASSWORD="$SA_PW" -e MSSQL_PID=Express \
    -p 127.0.0.1:1433:1433 \
    -v "$BAK_DIR:/var/opt/mssql/backup:ro" \
    -v "$EXPORT_ROOT/backup_pdp:/export/pdp" \
    -v "$EXPORT_ROOT/backup_sis:/export/sis" \
    "$MSSQL_IMAGE" >/dev/null
fi
sqlcmd() { docker exec "$CONTAINER" "$TOOLS/sqlcmd" -S localhost -U SA -P "$SA_PW" -C -b "$@"; }
log "Waiting for SQL Server..."
for i in $(seq 1 60); do
  if sqlcmd -Q "SELECT 1" >/dev/null 2>&1; then break; fi
  [ "$i" -lt 60 ] || die "SQL Server did not come up (docker logs $CONTAINER)"
  sleep 2
done

# ── Helpers ────────────────────────────────────────────────────────────────
restore_db() {  # restore_db <database> <bak file>
  local db="$1" bak="$2" moves="" name type ext i=0
  log "Restoring $db from $bak"
  while IFS='|' read -r name _ type _; do
    name="${name%"${name##*[! ]}"}"; type="${type%"${type##*[! ]}"}"
    [ -n "$name" ] || continue
    i=$((i + 1)); ext=mdf; [ "$type" = "L" ] && ext=ldf
    moves="$moves, MOVE '$name' TO '/var/opt/mssql/data/${db}_${i}.${ext}'"
  done < <(sqlcmd -h -1 -W -s '|' -Q "SET NOCOUNT ON; RESTORE FILELISTONLY FROM DISK = '/var/opt/mssql/backup/$bak'" | grep '|')
  [ -n "$moves" ] || die "could not read the file list of $bak"
  sqlcmd -Q "RESTORE DATABASE [$db] FROM DISK = '/var/opt/mssql/backup/$bak' WITH REPLACE${moves}" >/dev/null
  log "  $db restored"
}

export_tables() {  # export_tables <database> <export subdir>
  local db="$1" sub="$2" t name n=0
  log "Exporting every base table of $db to $EXPORT_ROOT/backup_$sub/"
  while read -r t; do
    t="${t%"${t##*[! ]}"}"; [ -n "$t" ] || continue
    name="${t#*.}"
    docker exec -u root "$CONTAINER" "$TOOLS/bcp" "$db.$t" out "/export/$sub/$name.csv" -c -t, -S localhost -U SA -P "$SA_PW" -u >/dev/null \
      || die "bcp failed on $db.$t"
    # Legacy char columns are NUL-padded; PostgreSQL rejects NUL in text, and
    # the converters do not strip it everywhere, so drop it at the source.
    docker exec -u root "$CONTAINER" sh -c "tr -d '\\000' < '/export/$sub/$name.csv' > '/export/$sub/.tmp' && mv '/export/$sub/.tmp' '/export/$sub/$name.csv'" \
      || die "NUL stripping failed on $name.csv"
    n=$((n + 1))
  done < <(sqlcmd -d "$db" -h -1 -W -Q "SET NOCOUNT ON; SELECT TABLE_SCHEMA + '.' + TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE = 'BASE TABLE' ORDER BY 1")
  # The converters read the corrected spelling of these two legacy table names.
  for t in Stone Product; do
    [ -f "$EXPORT_ROOT/backup_$sub/${t}Catagories.csv" ] \
      && docker exec -u root "$CONTAINER" mv "/export/$sub/${t}Catagories.csv" "/export/$sub/${t}Categories.csv"
  done
  log "  $n tables exported"
}

export_pictures() {
  log "Exporting photos and drawings to $EXPORT_ROOT/pictures/ (pyodbc in a temporary python container)"
  docker run --rm --network=host \
    -v "$REPO_DIR:/app" -v "$EXPORT_ROOT/pictures:/out" \
    -e PICTURES_OUT_DIR=/out \
    -e MSSQL_SERVER=127.0.0.1 -e MSSQL_PASSWORD="$SA_PW" \
    python:3.11-slim bash -c '
      apt-get update -qq && apt-get install -y -qq unixodbc unixodbc-dev freetds-dev tdsodbc gcc >/dev/null 2>&1
      pip install -q pyodbc tqdm
      cd /app && python3 ops/migration/export/export_pictures_products.py' \
    || die "picture export failed"
}

# ── Run ────────────────────────────────────────────────────────────────────
if [ "$WHAT" = pdp ] || [ "$WHAT" = all ]; then
  restore_db JMS_PDP21 "$(find_bak 'JMS-PDP21*.bak')"
  export_tables JMS_PDP21 pdp
fi
if [ "$WHAT" = sis ] || [ "$WHAT" = all ]; then
  restore_db JMS_SIS21 "$(find_bak 'JMS-SIS21*.bak')"
  export_tables JMS_SIS21 sis
fi
if [ "$WHAT" = pictures ] || [ "$WHAT" = all ]; then
  restore_db PICTURES "$(find_bak 'Pictures*.bak')"
  export_pictures
fi

if [ "$KEEP" = "--keep" ]; then
  log "Container $CONTAINER left running on 127.0.0.1:1433 — SA password: $SA_PW"
  log "  docker exec -it $CONTAINER $TOOLS/sqlcmd -S localhost -U SA -P '$SA_PW' -C"
  log "  docker rm -f $CONTAINER    # when done"
else
  docker rm -f "$CONTAINER" >/dev/null
  log "Container $CONTAINER removed"
fi
log "Done."
