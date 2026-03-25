#!/bin/bash
# Configure UFW (firewall) for the demo or production server.
# Usage: ./ops/setup_firewall.sh [demo|prod]
#   demo : open 22, 80, 443 — close 8070 (Odoo via tunnel only)
#   prod : open 22 (internal), 51820/udp (WireGuard) — block everything else
#
# WARNING: requires sudo. Verify SSH is allowed before enabling.

set -e

MODE="${1:-demo}"
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

if ! command -v ufw &>/dev/null; then
  echo "Installing ufw..."
  sudo apt-get install -y ufw
fi

echo -e "${YELLOW}=== Firewall configuration (mode: $MODE) ===${NC}"
echo ""
echo -e "${RED}WARNING: Verify your SSH session will remain active before continuing.${NC}"
echo "This script will enable UFW. If SSH (port 22) is not allowed, you will lose access."
echo ""
read -p "Continue? [y/N] " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
  echo "Cancelled."
  exit 0
fi

# ── Common rules ───────────────────────────────────────────────────────────
sudo ufw --force reset
sudo ufw default deny incoming
sudo ufw default allow outgoing

# SSH always open (prevents lockout)
sudo ufw allow 22/tcp comment 'SSH'

if [ "$MODE" = "demo" ]; then
  # ── Demo mode (Oracle Cloud VPS) ──────────────────────────────────────
  # Port 80/443 for future Let's Encrypt or nginx
  sudo ufw allow 80/tcp  comment 'HTTP (future HTTPS redirect)'
  sudo ufw allow 443/tcp comment 'HTTPS (future direct)'
  # Port 8070 intentionally CLOSED
  # cloudflared connects outbound (no inbound needed)
  echo ""
  echo "Demo rules applied:"
  echo "  ✓ 22/tcp   — SSH"
  echo "  ✓ 80/tcp   — HTTP (future Let's Encrypt)"
  echo "  ✓ 443/tcp  — HTTPS"
  echo "  ✗ 8070     — CLOSED (access via Cloudflare Tunnel only)"
  echo "  ✗ 5432     — CLOSED (PostgreSQL internal only)"

elif [ "$MODE" = "prod" ]; then
  # ── Production mode (on-premises server) ──────────────────────────────
  # 8069 from internal network only
  # Adjust 192.168.0.0/16 to match the actual company subnet
  sudo ufw allow from 192.168.0.0/16 to any port 8069 proto tcp comment 'Odoo (internal network)'
  # WireGuard VPN (UDP)
  sudo ufw allow 51820/udp comment 'WireGuard VPN'
  echo ""
  echo "Production rules applied:"
  echo "  ✓ 22/tcp          — SSH (all)"
  echo "  ✓ 8069/tcp        — Odoo (192.168.0.0/16 only)"
  echo "  ✓ 51820/udp       — WireGuard VPN"
  echo "  ✗ everything else — BLOCKED"
  echo ""
  echo -e "${YELLOW}Adjust the 192.168.0.0/16 subnet if needed.${NC}"

else
  echo "Unknown mode: $MODE (use 'demo' or 'prod')"
  exit 1
fi

# ── Enable UFW ─────────────────────────────────────────────────────────────
sudo ufw --force enable
echo ""
echo -e "${GREEN}UFW enabled.${NC}"
echo ""
sudo ufw status verbose
echo ""
echo -e "${YELLOW}Oracle Cloud reminder (demo mode):${NC}"
echo "In the Oracle Cloud console → Networking → Security Lists:"
echo "  - Open:  22/tcp, 80/tcp, 443/tcp"
echo "  - Close: 8070/tcp, 5432/tcp"
echo "See ops/SECURITY.md for detailed instructions."
