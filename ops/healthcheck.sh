#!/bin/bash
# Check the health of a Rubicon stack.
# Usage: ./ops/healthcheck.sh <dev|demo|prod>
# Exit code 0 if all OK, 1 if a problem is detected (warnings alone exit 0).
# Compatible with cron, Nagios, and UptimeRobot (via HTTP if exposed).

ENV="${1:-}"
PROBLEMS=()
WARNINGS=()

case "$ENV" in dev|demo|prod) ;; *) echo "Usage: $0 <dev|demo|prod>"; exit 1 ;; esac
# shellcheck source=lib/common.sh
source "$(dirname "$0")/lib/common.sh"
rubicon_env "$ENV" optional
MIN_DB_BYTES="${MIN_DB_BYTES:-200000}"


# ── 1. Odoo HTTP healthcheck ───────────────────────────────────────────────
if curl -sf "http://localhost:$PORT/web/health" > /dev/null 2>&1; then
  echo "✓ Odoo responding on port $PORT"
else
  PROBLEMS+=("Odoo not responding at http://localhost:$PORT/web/health")
fi

# ── 2/3. Containers ───────────────────────────────────────────────────────
for svc in "$ODOO_SERVICE" "$DB_SERVICE"; do
  if running "$svc"; then
    echo "✓ Container $svc running"
  else
    PROBLEMS+=("Container $svc is not running")
  fi
done

# ── 4. Disk space ─────────────────────────────────────────────────────────
DISK_USAGE=$(df / | tail -1 | awk '{print $5}' | tr -d '%')
if [ "$DISK_USAGE" -lt 80 ]; then
  echo "✓ Disk space OK (${DISK_USAGE}% used)"
elif [ "$DISK_USAGE" -lt 90 ]; then
  WARNINGS+=("Disk space at ${DISK_USAGE}% — cleanup recommended")
else
  PROBLEMS+=("Disk space critical: ${DISK_USAGE}% used")
fi

# ── 5. Backups: recent, valid, last run status, restore test ──────────────
if [ -d "$BACKUP_DIR" ]; then
  RECENT_BACKUP=$(find "$BACKUP_DIR" -name "${PREFIX}_db_*.sql.gz" -mmin -1500 2>/dev/null | sort | tail -1)
  if [ -n "$RECENT_BACKUP" ]; then
    if gzip -t "$RECENT_BACKUP" 2>/dev/null && [ "$(stat -c %s "$RECENT_BACKUP")" -ge "$MIN_DB_BYTES" ]; then
      echo "✓ Recent backup valid: $(basename "$RECENT_BACKUP") ($(du -h "$RECENT_BACKUP" | cut -f1))"
    else
      PROBLEMS+=("Latest backup $(basename "$RECENT_BACKUP") is corrupt or too small")
    fi
  else
    WARNINGS+=("No ${PREFIX} DB backup younger than 25h in $BACKUP_DIR")
  fi

  STATUS_FILE="$BACKUP_DIR/.last_status_${PREFIX}"
  if [ -f "$STATUS_FILE" ]; then
    case "$(cut -d' ' -f1 "$STATUS_FILE")" in
      OK)   echo "✓ Last backup run reported OK" ;;
      WARN) WARNINGS+=("Last backup run reported warnings: $(cat "$STATUS_FILE")") ;;
      *)    PROBLEMS+=("Last backup run FAILED: $(cat "$STATUS_FILE")") ;;
    esac
  fi

  VERIFY_MARKER="$BACKUP_DIR/.last_verify_ok_${ENV}"
  if [ -f "$VERIFY_MARKER" ] && [ -n "$(find "$VERIFY_MARKER" -mtime -8 2>/dev/null)" ]; then
    echo "✓ Restore test passed on $(date -r "$VERIFY_MARKER" '+%Y-%m-%d')"
  else
    WARNINGS+=("No successful restore test in the last 8 days (run ops/verify_backup.sh $ENV)")
  fi
else
  WARNINGS+=("Backup directory $BACKUP_DIR does not exist")
fi

# ── 6. WireGuard (only where it is configured) ────────────────────────────
if [ -f /etc/wireguard/wg0.conf ]; then
  if ip link show wg0 &>/dev/null; then
    WG_PEERS=$(sudo -n wg show wg0 2>/dev/null | grep -c "^peer" || echo "?")
    echo "✓ WireGuard wg0 active ($WG_PEERS peer(s))"
  else
    WARNINGS+=("WireGuard is configured but interface wg0 is down")
  fi
fi

# ── Summary ────────────────────────────────────────────────────────────────
echo ""
if [ ${#WARNINGS[@]} -gt 0 ]; then
  echo "⚠ WARNINGS:"
  for w in "${WARNINGS[@]}"; do echo "  - $w"; done
fi
if [ ${#PROBLEMS[@]} -gt 0 ]; then
  echo "✗ PROBLEMS DETECTED:"
  for p in "${PROBLEMS[@]}"; do echo "  - $p"; done
  exit 1
fi
echo "✓ All checks passed (env: $ENV)"
exit 0
