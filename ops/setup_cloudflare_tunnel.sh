#!/bin/bash
# Install cloudflared and start an anonymous HTTPS tunnel to Odoo demo.
# Usage: ./ops/setup_cloudflare_tunnel.sh [--service]
#   --service : install cloudflared as a persistent systemd service (restarts on boot)
#
# Without --service: runs the tunnel in the foreground (for testing).
# The https://*.trycloudflare.com URL is shown in the logs.
#
# IMPORTANT: after installation, add proxy_mode = True to odoo_demo.conf
# then restart odoo_demo.

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
AS_SERVICE="${1:-}"

# ── Pre-flight checks ──────────────────────────────────────────────────────
if ! command -v curl &>/dev/null; then
  echo "Error: curl is required" && exit 1
fi

# ── Install cloudflared ────────────────────────────────────────────────────
if command -v cloudflared &>/dev/null; then
  echo "cloudflared already installed: $(cloudflared --version)"
else
  echo "Installing cloudflared..."
  # Cloudflare GPG key
  curl -fsSL https://pkg.cloudflare.com/cloudflare-main.gpg \
    | sudo gpg --dearmor -o /usr/share/keyrings/cloudflare-main.gpg

  # APT source
  echo "deb [signed-by=/usr/share/keyrings/cloudflare-main.gpg] \
https://pkg.cloudflare.com/cloudflared $(lsb_release -cs) main" \
    | sudo tee /etc/apt/sources.list.d/cloudflared.list > /dev/null

  sudo apt-get update -qq
  sudo apt-get install -y cloudflared
  echo "cloudflared installed: $(cloudflared --version)"
fi

# ── Systemd service mode ───────────────────────────────────────────────────
if [ "$AS_SERVICE" = "--service" ]; then
  echo ""
  echo "Installing cloudflared systemd service..."
  echo "The tunnel will start automatically on server boot."
  echo ""

  # Create the service unit file
  sudo tee /etc/systemd/system/cloudflared-tunnel.service > /dev/null <<'UNIT'
[Unit]
Description=Cloudflare Tunnel (Rubicon demo)
After=network.target docker.service
Wants=network.target

[Service]
Type=simple
Restart=on-failure
RestartSec=5s
ExecStart=/usr/bin/cloudflared tunnel --url http://localhost:8070 --no-autoupdate
StandardOutput=journal
StandardError=journal
SyslogIdentifier=cloudflared-tunnel

[Install]
WantedBy=multi-user.target
UNIT

  sudo systemctl daemon-reload
  sudo systemctl enable cloudflared-tunnel
  sudo systemctl restart cloudflared-tunnel

  echo ""
  echo "Service started. Waiting for tunnel URL..."
  sleep 8
  echo ""
  echo "Tunnel URL (look for 'trycloudflare.com' in the logs):"
  sudo journalctl -u cloudflared-tunnel -n 30 --no-pager | grep -i "trycloudflare\|https://" || true
  echo ""
  echo "To follow logs live:"
  echo "  sudo journalctl -u cloudflared-tunnel -f"
  echo ""
  echo "REMINDER: add 'proxy_mode = True' to odoo_conf/odoo_demo.conf"
  echo "then: docker compose -f docker-compose.demo.yml restart odoo_demo"

else
  # ── Foreground mode (test) ─────────────────────────────────────────────
  echo ""
  echo "Starting tunnel in foreground (Ctrl+C to stop)..."
  echo "The https://*.trycloudflare.com URL will appear in a few seconds."
  echo ""
  cloudflared tunnel --url http://localhost:8070 --no-autoupdate
fi
