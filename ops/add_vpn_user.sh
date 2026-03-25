#!/bin/bash
# Add a WireGuard VPN user.
# Usage: ./ops/add_vpn_user.sh <first_last>
# Example: ./ops/add_vpn_user.sh john_doe
#
# Generates the client configuration and displays it as a QR code (mobile) and plain text.
# The peer is automatically added to /etc/wireguard/wg0.conf.

set -e

USERNAME="$1"
if [ -z "$USERNAME" ]; then
  echo "Usage: $0 <first_last>"
  echo "Example: $0 john_doe"
  exit 1
fi

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

KEYS_DIR="/etc/wireguard/keys"
WG_CONF="/etc/wireguard/wg0.conf"
USER_DIR="$KEYS_DIR/users/$USERNAME"

# ── Check WireGuard is installed ───────────────────────────────────────────
if [ ! -f "$WG_CONF" ]; then
  echo "WireGuard not configured. Run first: ./ops/setup_wireguard.sh"
  exit 1
fi

# ── Find the next available IP in 10.8.0.0/24 ─────────────────────────────
LAST_IP=$(grep -oP "AllowedIPs = 10\.8\.0\.\K\d+" "$WG_CONF" 2>/dev/null | sort -n | tail -1 || echo "1")
NEXT_IP=$((LAST_IP + 1))
if [ "$NEXT_IP" -gt 254 ]; then
  echo "Error: all VPN IPs are in use (max 253 users)."
  exit 1
fi
CLIENT_IP="10.8.0.$NEXT_IP"

# ── Get server info ────────────────────────────────────────────────────────
SERVER_PUBLIC=$(sudo cat "$KEYS_DIR/server_public.key")
SERVER_ADDR=$(hostname -I | awk '{print $1}')

# ── Generate client keys ───────────────────────────────────────────────────
sudo mkdir -p "$USER_DIR"
sudo chmod 700 "$USER_DIR"

wg genkey | sudo tee "$USER_DIR/private.key" > /dev/null
sudo wg pubkey < "$USER_DIR/private.key" | sudo tee "$USER_DIR/public.key" > /dev/null
wg genpsk | sudo tee "$USER_DIR/preshared.key" > /dev/null
sudo chmod 600 "$USER_DIR/private.key" "$USER_DIR/preshared.key"

CLIENT_PRIVATE=$(sudo cat "$USER_DIR/private.key")
CLIENT_PUBLIC=$(sudo cat "$USER_DIR/public.key")
CLIENT_PSK=$(sudo cat "$USER_DIR/preshared.key")

# ── Create client config file ──────────────────────────────────────────────
CLIENT_CONF="$USER_DIR/${USERNAME}.conf"
sudo tee "$CLIENT_CONF" > /dev/null <<CONF
[Interface]
PrivateKey = $CLIENT_PRIVATE
Address = $CLIENT_IP/24
DNS = 10.8.0.1

[Peer]
PublicKey = $SERVER_PUBLIC
PresharedKey = $CLIENT_PSK
Endpoint = $SERVER_ADDR:51820
AllowedIPs = 10.8.0.0/24, 192.168.0.0/16
PersistentKeepalive = 25
CONF

sudo chmod 600 "$CLIENT_CONF"

# ── Add peer to wg0.conf ───────────────────────────────────────────────────
sudo tee -a "$WG_CONF" > /dev/null <<PEER

[Peer]
# User: $USERNAME ($CLIENT_IP)
PublicKey = $CLIENT_PUBLIC
PresharedKey = $CLIENT_PSK
AllowedIPs = $CLIENT_IP/32
PEER

# ── Reload WireGuard (without dropping active connections) ─────────────────
sudo wg addconf wg0 <(sudo wg-quick strip wg0 2>/dev/null || true) 2>/dev/null || \
  sudo systemctl reload wg-quick@wg0 2>/dev/null || \
  sudo wg set wg0 peer "$CLIENT_PUBLIC" preshared-key "$USER_DIR/preshared.key" allowed-ips "$CLIENT_IP/32"

echo -e "${GREEN}=== VPN user '$USERNAME' created ===${NC}"
echo "  VPN client IP : $CLIENT_IP"
echo "  Client config : $CLIENT_CONF"
echo ""

# ── Display QR code (for mobile) ──────────────────────────────────────────
if command -v qrencode &>/dev/null; then
  echo -e "${YELLOW}QR Code (import in the WireGuard app on mobile):${NC}"
  sudo qrencode -t ansiutf8 < "$CLIENT_CONF"
  echo ""
fi

echo -e "${YELLOW}Plain text config (for manual import on Windows/Mac):${NC}"
echo "File: $CLIENT_CONF"
echo ""
sudo cat "$CLIENT_CONF"
echo ""
echo "See ops/VPN_GUIDE.md for client installation instructions."
