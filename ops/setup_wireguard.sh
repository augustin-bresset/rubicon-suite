#!/bin/bash
# Configure WireGuard VPN on the production server.
# Enables secure remote access for off-site employees to Odoo.
# Usage: ./ops/setup_wireguard.sh
#
# Prerequisites: Ubuntu/Debian, sudo access, network interface eth0 (adjust if needed)
# After installation: add users with ./ops/add_vpn_user.sh <name>

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# ── Detect main network interface ─────────────────────────────────────────
MAIN_IF=$(ip route get 8.8.8.8 2>/dev/null | awk '{print $5; exit}' || echo "eth0")
SERVER_IP=$(hostname -I | awk '{print $1}')
WG_CONF="/etc/wireguard/wg0.conf"
KEYS_DIR="/etc/wireguard/keys"

echo -e "${GREEN}=== WireGuard VPN Installation ===${NC}"
echo "Network interface : $MAIN_IF"
echo "Server local IP   : $SERVER_IP"
echo "VPN network       : 10.8.0.0/24"
echo ""

# ── Installation ──────────────────────────────────────────────────────────
sudo apt-get update -qq
sudo apt-get install -y wireguard qrencode

# ── Generate server keys ───────────────────────────────────────────────────
sudo mkdir -p "$KEYS_DIR"
sudo chmod 700 "$KEYS_DIR"

if [ ! -f "$KEYS_DIR/server_private.key" ]; then
  wg genkey | sudo tee "$KEYS_DIR/server_private.key" > /dev/null
  sudo wg pubkey < "$KEYS_DIR/server_private.key" | sudo tee "$KEYS_DIR/server_public.key" > /dev/null
  sudo chmod 600 "$KEYS_DIR/server_private.key"
  echo "Server keys generated."
else
  echo "Existing server keys retained."
fi

SERVER_PRIVATE=$(sudo cat "$KEYS_DIR/server_private.key")
SERVER_PUBLIC=$(sudo cat "$KEYS_DIR/server_public.key")

# ── Enable IP forwarding ───────────────────────────────────────────────────
if ! grep -q "^net.ipv4.ip_forward=1" /etc/sysctl.conf; then
  echo "net.ipv4.ip_forward=1" | sudo tee -a /etc/sysctl.conf > /dev/null
  sudo sysctl -p > /dev/null
fi

# ── Create /etc/wireguard/wg0.conf ────────────────────────────────────────
if [ -f "$WG_CONF" ]; then
  echo -e "${YELLOW}Existing wg0.conf backed up → ${WG_CONF}.bak${NC}"
  sudo cp "$WG_CONF" "${WG_CONF}.bak"
fi

sudo tee "$WG_CONF" > /dev/null <<CONF
[Interface]
PrivateKey = $SERVER_PRIVATE
Address = 10.8.0.1/24
ListenPort = 51820
# Routing: VPN clients can access the internal network
PostUp   = iptables -A FORWARD -i wg0 -j ACCEPT; iptables -A FORWARD -o wg0 -j ACCEPT; iptables -t nat -A POSTROUTING -o $MAIN_IF -j MASQUERADE
PostDown = iptables -D FORWARD -i wg0 -j ACCEPT; iptables -D FORWARD -o wg0 -j ACCEPT; iptables -t nat -D POSTROUTING -o $MAIN_IF -j MASQUERADE

# ── Add user peers below (see ops/add_vpn_user.sh) ──
CONF

sudo chmod 600 "$WG_CONF"

# ── Enable and start ───────────────────────────────────────────────────────
sudo systemctl enable wg-quick@wg0
sudo systemctl restart wg-quick@wg0

echo ""
echo -e "${GREEN}WireGuard installed and started.${NC}"
echo ""
echo "Server public key (note this down):"
echo "  $SERVER_PUBLIC"
echo ""
echo "VPN server IP: 10.8.0.1"
echo ""
echo "Next steps:"
echo "  1. Configure UFW: ./ops/setup_firewall.sh prod"
echo "  2. Add users: ./ops/add_vpn_user.sh <first_last>"
echo "  3. Send QR code configs to employees (see ops/VPN_GUIDE.md)"
