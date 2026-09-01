#!/bin/bash
# Shared helpers for the stack lifecycle scripts (backup, restore, verify,
# healthcheck, init). Not a standalone script:
#
#   source "$(dirname "$0")/lib/common.sh"
#   rubicon_env <dev|demo|prod> [optional]
#
# rubicon_env sets, for the chosen environment:
#   REPO_DIR COMPOSE_FILE ENV_FILE DB_SERVICE ODOO_SERVICE PORT FALLBACK_VOLUME
#   CONFIG_FILES (array of files to include in the config backup)  PREFIX
#   DB_NAME DB_USER BACKUP_DIR OCI_BUCKET BACKUP_AGE_RECIPIENT
# The last five come from the env file (.env, .env.demo, .env.prod). Values
# already present in the process environment win over the file, so
# `BACKUP_DIR=/mnt/x ./ops/backup.sh prod` does what it says. With "optional"
# a missing env file is tolerated (healthcheck).
#
# Helpers:
#   die MSG...         print "ERROR: MSG" on stderr and exit 1
#   compose ARGS...    docker compose -f "$COMPOSE_FILE" ARGS
#   running SERVICE    true when that compose service is running
#   resolve_volume     name of the volume mounted on Odoo's data dir (fallback: FALLBACK_VOLUME)
#   odoo_cli ARGS...   run `odoo ARGS` inside the running odoo container, or in a one-off one

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

die() { echo "ERROR: $*" >&2; exit 1; }

# The variables below are consumed by the sourcing scripts, not here.
# shellcheck disable=SC2034
rubicon_env() {
  local env="${1:-}" optional="${2:-}"
  local pre_backup_dir="${BACKUP_DIR:-}" pre_bucket="${OCI_BUCKET:-}" pre_recipient="${BACKUP_AGE_RECIPIENT:-}"
  case "$env" in
    dev)
      COMPOSE_FILE="$REPO_DIR/docker-compose.yml";      ENV_FILE="$REPO_DIR/.env"
      DB_SERVICE="db";      ODOO_SERVICE="odoo";      PORT=8069
      FALLBACK_VOLUME="rubicon-suite_odoo_data";       CONFIG_FILES=(".env" "odoo_conf/odoo.conf") ;;
    demo)
      COMPOSE_FILE="$REPO_DIR/docker-compose.demo.yml"; ENV_FILE="$REPO_DIR/.env.demo"
      DB_SERVICE="db_demo"; ODOO_SERVICE="odoo_demo"; PORT=8070
      FALLBACK_VOLUME="rubicon-suite_odoo_demo_data";  CONFIG_FILES=(".env.demo" "odoo_conf/odoo_demo.conf") ;;
    prod)
      COMPOSE_FILE="$REPO_DIR/docker-compose.prod.yml"; ENV_FILE="$REPO_DIR/.env.prod"
      DB_SERVICE="db";      ODOO_SERVICE="odoo";      PORT=8069
      FALLBACK_VOLUME="rubicon-suite_prod_odoo_data";  CONFIG_FILES=(".env.prod" "odoo_conf/odoo.prod.conf") ;;
    *) die "unknown environment '$env' (expected dev, demo or prod)" ;;
  esac
  PREFIX="$env"
  if [ -f "$ENV_FILE" ]; then
    # shellcheck disable=SC1090
    source "$ENV_FILE"
  elif [ "$optional" != "optional" ]; then
    die "$ENV_FILE not found (copy the matching .example file and fill it in)"
  fi
  DB_NAME="${POSTGRES_DB:-${DB_NAME:-rubicon}}"
  DB_USER="${POSTGRES_USER:-${DB_USER:-odoo}}"
  BACKUP_DIR="${pre_backup_dir:-${BACKUP_DIR:-/opt/rubicon-backups}}"
  OCI_BUCKET="${pre_bucket:-${OCI_BUCKET:-}}"
  BACKUP_AGE_RECIPIENT="${pre_recipient:-${BACKUP_AGE_RECIPIENT:-}}"
  export DB_NAME DB_USER BACKUP_DIR OCI_BUCKET BACKUP_AGE_RECIPIENT
}

compose() { docker compose -f "$COMPOSE_FILE" "$@"; }

running() { compose ps --status running --services 2>/dev/null | grep -qx "$1"; }

resolve_volume() {
  local cid name=""
  cid=$(compose ps -a -q "$ODOO_SERVICE" 2>/dev/null | head -1)
  if [ -n "$cid" ]; then
    name=$(docker inspect -f '{{range .Mounts}}{{if eq .Destination "/var/lib/odoo/.local/share/Odoo"}}{{.Name}}{{end}}{{end}}' "$cid" 2>/dev/null || true)
  fi
  echo "${name:-$FALLBACK_VOLUME}"
}

odoo_cli() {
  if running "$ODOO_SERVICE"; then
    compose exec -T "$ODOO_SERVICE" odoo "$@"
  else
    compose run --rm --no-deps -T "$ODOO_SERVICE" odoo "$@"
  fi
}
