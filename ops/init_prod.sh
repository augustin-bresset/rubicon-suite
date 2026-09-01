#!/bin/bash
# First boot of a stack: create the Odoo database, install the Rubicon
# modules without demo data, set the administrator password, start the stack.
#
# Usage: ./ops/init_prod.sh [--env prod] [--db NAME] [--modules a,b,c] [--admin-login LOGIN]
#   --env          dev | demo | prod (default: prod)
#   --db           database name (default: the environment's POSTGRES_DB)
#   --modules      comma-separated modules to install (default: the suite,
#                  PCS modules added when present in rubicon_addons/)
#   --admin-login  login of the administrator account (default: admin)
# The administrator password is read from ADMIN_PASSWORD or prompted (twice,
# hidden). It must be at least 12 characters.
#
# Refuses to run when the database already exists (use ops/restore.sh for
# that) or when .env.<env> / the Odoo config still contain CHANGE_ME.
# `rubicon_demo` is never installed here: its pre_init_hook deletes every
# product model, SIS document and partner of the database.

set -euo pipefail

ENV="prod"; TARGET_DB=""; MODULES=""; ADMIN_LOGIN="admin"
usage() { echo "Usage: $0 [--env prod] [--db NAME] [--modules a,b,c] [--admin-login LOGIN]" >&2; exit 1; }
while [ $# -gt 0 ]; do
  case "$1" in
    --env)         ENV="${2:-}"; shift ;;
    --db)          TARGET_DB="${2:-}"; shift ;;
    --modules)     MODULES="${2:-}"; shift ;;
    --admin-login) ADMIN_LOGIN="${2:-}"; shift ;;
    *) usage ;;
  esac
  shift
done

# shellcheck source=lib/common.sh
source "$(dirname "$0")/lib/common.sh"
rubicon_env "$ENV"
TARGET_DB="${TARGET_DB:-$DB_NAME}"
[[ "$TARGET_DB" =~ ^[A-Za-z0-9_]+$ ]] || die "invalid database name: $TARGET_DB"
[[ "$ADMIN_LOGIN" =~ ^[A-Za-z0-9_.@-]+$ ]] || die "invalid admin login: $ADMIN_LOGIN"

if [ -z "$MODULES" ]; then
  MODULES="rubicon_env,rubicon_uom,pdp_frontend,pdp_metal_market,sis_frontend,sis_analysis,rubicon_storage"
  for m in pcs_frontend pcs_simulator ps_utilities sis_report; do
    [ -d "$REPO_DIR/rubicon_addons/$m" ] && MODULES="$MODULES,$m"
  done
fi
case ",$MODULES," in *,rubicon_demo,*) die "rubicon_demo must never be installed on a real database" ;; esac

# ── Configuration sanity ───────────────────────────────────────────────────
grep -q "CHANGE_ME" "$ENV_FILE" && die "$ENV_FILE still contains CHANGE_ME values"
if [ "$ENV" = prod ]; then
  CONF="$REPO_DIR/odoo_conf/odoo.prod.conf"
  [ -f "$CONF" ] || die "$CONF not found (copy odoo_conf/odoo.conf.prod.example and fill it in)"
  grep -q "CHANGE_ME" "$CONF" && die "$CONF still contains CHANGE_ME values"
  grep -qE "^\s*list_db\s*=\s*False" "$CONF" || die "$CONF must set list_db = False"
  grep -qE "^\s*logfile\s*=" "$CONF" && die "$CONF must not set logfile (logs go to stdout, see docker-compose.prod.yml)"
fi

# ── Administrator password ─────────────────────────────────────────────────
if [ -z "${ADMIN_PASSWORD:-}" ]; then
  read -r -s -p "Administrator password for '$ADMIN_LOGIN': " ADMIN_PASSWORD; echo
  read -r -s -p "Repeat: " ADMIN_PASSWORD2; echo
  [ "$ADMIN_PASSWORD" = "$ADMIN_PASSWORD2" ] || die "passwords do not match"
fi
[ "${#ADMIN_PASSWORD}" -ge 12 ] || die "the administrator password must be at least 12 characters"

# ── Database server ────────────────────────────────────────────────────────
echo "Starting $DB_SERVICE..."
compose up -d "$DB_SERVICE" >/dev/null
for i in $(seq 1 30); do
  compose exec -T "$DB_SERVICE" pg_isready -U "$DB_USER" -d postgres >/dev/null 2>&1 && break
  [ "$i" -lt 30 ] || die "PostgreSQL did not become ready"
  sleep 2
done
if compose exec -T "$DB_SERVICE" psql -Atq -U "$DB_USER" -d postgres -c "SELECT 1 FROM pg_database WHERE datname = '$TARGET_DB'" | grep -q 1; then
  die "database $TARGET_DB already exists — this script only initialises a new one (see ops/restore.sh)"
fi

# ── Install ────────────────────────────────────────────────────────────────
echo "Installing into $TARGET_DB: $MODULES"
echo "(a few minutes; the log is on stdout)"
compose run --rm --no-deps -T "$ODOO_SERVICE" odoo -d "$TARGET_DB" -i "$MODULES" \
  --without-demo=all --stop-after-init --workers=0 --max-cron-threads=0 \
  || die "module installation failed"

# ── Administrator account ──────────────────────────────────────────────────
echo "Setting the administrator account ($ADMIN_LOGIN)..."
# The password travels as an environment variable passed by name (-e VAR), so
# it never appears on a command line; the one-off container is removed after.
RUBICON_ADMIN_PASSWORD="$ADMIN_PASSWORD" compose run --rm --no-deps -T -e RUBICON_ADMIN_PASSWORD "$ODOO_SERVICE" \
  odoo shell -d "$TARGET_DB" --no-http --workers=0 --max-cron-threads=0 <<PY >/dev/null
import os
admin = env.ref('base.user_admin')
admin.write({'login': '$ADMIN_LOGIN', 'password': os.environ['RUBICON_ADMIN_PASSWORD']})
env.cr.commit()
PY

# ── Start ──────────────────────────────────────────────────────────────────
echo "Starting the stack..."
compose up -d >/dev/null
for i in $(seq 1 40); do
  curl -sf "http://127.0.0.1:$PORT/web/health" >/dev/null 2>&1 && break
  [ "$i" -lt 40 ] || echo "WARNING: Odoo not answering yet on 127.0.0.1:$PORT (docker compose -f $COMPOSE_FILE logs $ODOO_SERVICE)"
  sleep 3
done

cat <<NEXT

Database $TARGET_DB initialised. Next steps:
  1. Put the reverse proxy in front (ops/server/nginx_prod.conf or a named
     Cloudflare tunnel); Odoo only listens on 127.0.0.1:$PORT.
  2. Log in as '$ADMIN_LOGIN', enable two-factor authentication
     (Preferences > Account Security), then create one named user per person
     with the Rubicon access groups — never share the administrator account.
  3. Load the data: ops/restore.sh (from a backup) or ops/migration/README.md
     (from the legacy .bak files).
  4. Install the crons (ops/CRON.md) and run ./ops/backup.sh $ENV once.
NEXT
