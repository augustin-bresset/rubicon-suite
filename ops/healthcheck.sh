#!/bin/bash
# Check the health status of the Rubicon server.
# Usage: ./ops/healthcheck.sh [demo|prod]
# Returns exit code 0 if all OK, 1 if a problem is detected.
# Compatible with cron, Nagios, and UptimeRobot (via HTTP if exposed).

ENV="${1:-demo}"

SCRIPT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
PROBLEMS=()
WARNINGS=()

# ── Environment parameters ─────────────────────────────────────────────────
if [ "$ENV" = "demo" ]; then
  COMPOSE_FILE="$SCRIPT_DIR/docker-compose.demo.yml"
  ODOO_SERVICE="odoo_demo"
  DB_SERVICE="db_demo"
  PORT=8070
  PREFIX="demo"
elif [ "$ENV" = "prod" ]; then
  COMPOSE_FILE="$SCRIPT_DIR/docker-compose.yml"
  ODOO_SERVICE="odoo"
  DB_SERVICE="db"
  PORT=8069
  PREFIX="prod"
else
  echo "Usage: $0 [demo|prod]"
  exit 1
fi

BACKUP_DIR="/opt/rubicon-backups"

# ── 1. Odoo HTTP healthcheck ───────────────────────────────────────────────
if curl -sf "http://localhost:$PORT/web/health" > /dev/null 2>&1; then
  echo "✓ Odoo responding on port $PORT"
else
  PROBLEMS+=("Odoo not responding at http://localhost:$PORT/web/health")
fi

# ── 2. Odoo container running ─────────────────────────────────────────────
if docker compose -f "$COMPOSE_FILE" ps "$ODOO_SERVICE" 2>/dev/null | grep -qiE "running|up"; then
  echo "✓ Container $ODOO_SERVICE running"
else
  PROBLEMS+=("Container $ODOO_SERVICE is not in 'running' state")
fi

# ── 3. DB container running ───────────────────────────────────────────────
if docker compose -f "$COMPOSE_FILE" ps "$DB_SERVICE" 2>/dev/null | grep -qiE "running|up"; then
  echo "✓ Container $DB_SERVICE running"
else
  PROBLEMS+=("Container $DB_SERVICE is not in 'running' state")
fi

# ── 4. Disk space ─────────────────────────────────────────────────────────
DISK_USAGE=$(df / | tail -1 | awk '{print $5}' | tr -d '%')
if [ "$DISK_USAGE" -lt 80 ]; then
  echo "✓ Disk space OK (${DISK_USAGE}% used)"
elif [ "$DISK_USAGE" -lt 90 ]; then
  WARNINGS+=("Disk space at ${DISK_USAGE}% — cleanup recommended")
else
  PROBLEMS+=("Disk space critical: ${DISK_USAGE}% used")
fi

# ── 5. Recent backup (< 25h) ──────────────────────────────────────────────
if [ -d "$BACKUP_DIR" ]; then
  RECENT_BACKUP=$(find "$BACKUP_DIR" -name "${PREFIX}_db_*.sql.gz" -mtime -1 2>/dev/null | head -1)
  if [ -n "$RECENT_BACKUP" ]; then
    echo "✓ Recent backup found: $(basename "$RECENT_BACKUP")"
  else
    WARNINGS+=("No DB backup found in the last 25h in $BACKUP_DIR")
  fi
else
  WARNINGS+=("Backup directory $BACKUP_DIR does not exist")
fi

# ── 6. WireGuard (production only) ────────────────────────────────────────
if [ "$ENV" = "prod" ]; then
  if ip link show wg0 &>/dev/null; then
    WG_PEERS=$(sudo wg show wg0 2>/dev/null | grep -c "^peer" || echo "0")
    echo "✓ WireGuard wg0 active ($WG_PEERS peer(s))"
  else
    WARNINGS+=("WireGuard interface wg0 is inactive")
  fi
fi

# ── Summary ────────────────────────────────────────────────────────────────
echo ""

if [ ${#WARNINGS[@]} -gt 0 ]; then
  echo "⚠ WARNINGS:"
  for w in "${WARNINGS[@]}"; do
    echo "  - $w"
  done
fi

if [ ${#PROBLEMS[@]} -gt 0 ]; then
  echo "✗ PROBLEMS DETECTED:"
  for p in "${PROBLEMS[@]}"; do
    echo "  - $p"
  done
  exit 1
else
  echo "✓ All checks passed (env: $ENV)"
  exit 0
fi
