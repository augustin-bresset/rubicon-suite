#!/usr/bin/env bash
set -euo pipefail

# Raccourcis sûrs (TTY off)
DCX="docker compose exec -T"
ODOO="$DCX odoo"
DB="$DCX db"

# Aides
py() { $ODOO python3 - <<'PY'
$1
PY
}

psql() { $DB psql -U rubicondev -d rubicon -c "$1"; }
