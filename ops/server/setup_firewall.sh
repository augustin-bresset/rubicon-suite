#!/bin/bash
# Configure UFW for a Rubicon host.
# Usage: ./ops/server/setup_firewall.sh <online|demo|lan>
#   online : Internet-facing production server. Allows 22 (SSH), 80 and 443
#            (nginx). Odoo itself binds to 127.0.0.1 (docker-compose.prod.yml)
#            and is only reachable through the reverse proxy or tunnel.
#            SSH_ALLOW_FROM=<CIDR> restricts SSH to that network (recommended
#            when the team has a fixed IP or a VPN exit).
#   demo   : demo VPS behind a Cloudflare tunnel. Allows 22, 80, 443; 8070 stays closed.
#   lan    : on-premises server on a company network. Allows 22, Odoo 8069
#            from LAN_CIDR (default 192.168.0.0/16) and WireGuard 51820/udp.
#
# Docker publishes ports with NAT rules that bypass UFW: only ports bound to
# 127.0.0.1 in the compose files are truly private. docker-compose.prod.yml
# and docker-compose.demo.yml both bind to loopback.
#
# WARNING: requires sudo. Make sure your SSH key works before enabling.

set -euo pipefail

MODE="${1:-}"
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'
case "$MODE" in online|demo|lan) ;; *) echo "Usage: $0 <online|demo|lan>" >&2; exit 1 ;; esac

if ! command -v ufw &>/dev/null; then
  echo "Installing ufw..."
  sudo apt-get install -y ufw
fi

echo -e "${YELLOW}=== Firewall configuration (mode: $MODE) ===${NC}"
echo -e "${RED}WARNING: this resets UFW. If SSH (port 22) is blocked you lose access.${NC}"
read -r -p "Continue? [y/N] " REPLY
[[ $REPLY =~ ^[Yy]$ ]] || { echo "Cancelled."; exit 0; }

sudo ufw --force reset
sudo ufw default deny incoming
sudo ufw default allow outgoing

case "$MODE" in
  online)
    if [ -n "${SSH_ALLOW_FROM:-}" ]; then
      sudo ufw allow from "$SSH_ALLOW_FROM" to any port 22 proto tcp comment 'SSH (restricted)'
    else
      sudo ufw limit 22/tcp comment 'SSH (rate limited)'
    fi
    sudo ufw allow 80/tcp  comment 'HTTP (redirect + ACME)'
    sudo ufw allow 443/tcp comment 'HTTPS (nginx -> Odoo)'
    echo "Online rules: 22 ${SSH_ALLOW_FROM:+from $SSH_ALLOW_FROM }, 80, 443 — everything else blocked."
    echo "Odoo (8069/8072) and PostgreSQL (5432) are not published on any interface."
    ;;
  demo)
    sudo ufw limit 22/tcp comment 'SSH (rate limited)'
    sudo ufw allow 80/tcp  comment 'HTTP'
    sudo ufw allow 443/tcp comment 'HTTPS'
    echo "Demo rules: 22, 80, 443 — 8070 stays closed (Cloudflare tunnel connects outbound)."
    ;;
  lan)
    LAN_CIDR="${LAN_CIDR:-192.168.0.0/16}"
    sudo ufw allow 22/tcp comment 'SSH'
    sudo ufw allow from "$LAN_CIDR" to any port 8069 proto tcp comment 'Odoo (LAN)'
    sudo ufw allow 51820/udp comment 'WireGuard VPN'
    echo "LAN rules: 22, 8069 from $LAN_CIDR, 51820/udp — everything else blocked."
    ;;
esac

sudo ufw --force enable
echo -e "${GREEN}UFW enabled.${NC}"
sudo ufw status verbose
echo ""
echo -e "${YELLOW}Cloud provider reminder:${NC} mirror these rules in the provider firewall / security list"
echo "(Oracle: Networking > Virtual Cloud Networks > Security Lists). See ops/SECURITY.md."
