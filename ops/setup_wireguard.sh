#!/bin/bash
# Configure WireGuard VPN sur le serveur de production.
# Permet l'accès distant sécurisé des employés nomades à Odoo.
# Usage: ./ops/setup_wireguard.sh
#
# Prérequis: Ubuntu/Debian, accès sudo, interface réseau eth0 (adapter si nécessaire)
# Après installation: ajouter des utilisateurs avec ./ops/add_vpn_user.sh <nom>

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# ── Détecter l'interface réseau principale ────────────────────────────────
MAIN_IF=$(ip route get 8.8.8.8 2>/dev/null | awk '{print $5; exit}' || echo "eth0")
SERVER_IP=$(hostname -I | awk '{print $1}')
WG_CONF="/etc/wireguard/wg0.conf"
KEYS_DIR="/etc/wireguard/keys"

echo -e "${GREEN}=== Installation WireGuard VPN ===${NC}"
echo "Interface réseau : $MAIN_IF"
echo "IP serveur local : $SERVER_IP"
echo "Réseau VPN       : 10.8.0.0/24"
echo ""

# ── Installation ──────────────────────────────────────────────────────────
sudo apt-get update -qq
sudo apt-get install -y wireguard qrencode

# ── Génération des clés serveur ───────────────────────────────────────────
sudo mkdir -p "$KEYS_DIR"
sudo chmod 700 "$KEYS_DIR"

if [ ! -f "$KEYS_DIR/server_private.key" ]; then
  wg genkey | sudo tee "$KEYS_DIR/server_private.key" > /dev/null
  sudo wg pubkey < "$KEYS_DIR/server_private.key" | sudo tee "$KEYS_DIR/server_public.key" > /dev/null
  sudo chmod 600 "$KEYS_DIR/server_private.key"
  echo "Clés serveur générées."
else
  echo "Clés serveur existantes conservées."
fi

SERVER_PRIVATE=$(sudo cat "$KEYS_DIR/server_private.key")
SERVER_PUBLIC=$(sudo cat "$KEYS_DIR/server_public.key")

# ── Activer IP forwarding ─────────────────────────────────────────────────
if ! grep -q "^net.ipv4.ip_forward=1" /etc/sysctl.conf; then
  echo "net.ipv4.ip_forward=1" | sudo tee -a /etc/sysctl.conf > /dev/null
  sudo sysctl -p > /dev/null
fi

# ── Créer /etc/wireguard/wg0.conf ─────────────────────────────────────────
if [ -f "$WG_CONF" ]; then
  echo -e "${YELLOW}wg0.conf existant sauvegardé → ${WG_CONF}.bak${NC}"
  sudo cp "$WG_CONF" "${WG_CONF}.bak"
fi

sudo tee "$WG_CONF" > /dev/null <<CONF
[Interface]
PrivateKey = $SERVER_PRIVATE
Address = 10.8.0.1/24
ListenPort = 51820
# Routing : les clients VPN peuvent accéder au réseau interne
PostUp   = iptables -A FORWARD -i wg0 -j ACCEPT; iptables -A FORWARD -o wg0 -j ACCEPT; iptables -t nat -A POSTROUTING -o $MAIN_IF -j MASQUERADE
PostDown = iptables -D FORWARD -i wg0 -j ACCEPT; iptables -D FORWARD -o wg0 -j ACCEPT; iptables -t nat -D POSTROUTING -o $MAIN_IF -j MASQUERADE

# ── Ajouter les peers utilisateurs ci-dessous (voir ops/add_vpn_user.sh) ──
CONF

sudo chmod 600 "$WG_CONF"

# ── Activer et démarrer ───────────────────────────────────────────────────
sudo systemctl enable wg-quick@wg0
sudo systemctl restart wg-quick@wg0

echo ""
echo -e "${GREEN}WireGuard installé et démarré.${NC}"
echo ""
echo "Clé publique serveur (à noter) :"
echo "  $SERVER_PUBLIC"
echo ""
echo "IP VPN serveur : 10.8.0.1"
echo ""
echo "Prochaines étapes :"
echo "  1. Configurer UFW : ./ops/setup_firewall.sh prod"
echo "  2. Ajouter des utilisateurs : ./ops/add_vpn_user.sh <prenom_nom>"
echo "  3. Distribuer les configs QR code aux employés (voir ops/VPN_GUIDE.md)"
