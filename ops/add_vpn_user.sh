#!/bin/bash
# Ajoute un utilisateur WireGuard VPN.
# Usage: ./ops/add_vpn_user.sh <prenom_nom>
# Exemple: ./ops/add_vpn_user.sh jean_dupont
#
# Génère la configuration client et l'affiche en QR code (mobile) et en texte.
# Le peer est automatiquement ajouté à /etc/wireguard/wg0.conf.

set -e

USERNAME="$1"
if [ -z "$USERNAME" ]; then
  echo "Usage: $0 <prenom_nom>"
  echo "Exemple: $0 jean_dupont"
  exit 1
fi

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

KEYS_DIR="/etc/wireguard/keys"
WG_CONF="/etc/wireguard/wg0.conf"
USER_DIR="$KEYS_DIR/users/$USERNAME"

# ── Vérifier que WireGuard est installé ───────────────────────────────────
if [ ! -f "$WG_CONF" ]; then
  echo "WireGuard non configuré. Lancer d'abord: ./ops/setup_wireguard.sh"
  exit 1
fi

# ── Trouver la prochaine IP disponible dans 10.8.0.0/24 ───────────────────
LAST_IP=$(grep -oP "AllowedIPs = 10\.8\.0\.\K\d+" "$WG_CONF" 2>/dev/null | sort -n | tail -1 || echo "1")
NEXT_IP=$((LAST_IP + 1))
if [ "$NEXT_IP" -gt 254 ]; then
  echo "Erreur: toutes les IPs VPN sont utilisées (max 253 utilisateurs)."
  exit 1
fi
CLIENT_IP="10.8.0.$NEXT_IP"

# ── Récupérer les infos serveur ───────────────────────────────────────────
SERVER_PUBLIC=$(sudo cat "$KEYS_DIR/server_public.key")
SERVER_ADDR=$(hostname -I | awk '{print $1}')

# ── Générer les clés client ───────────────────────────────────────────────
sudo mkdir -p "$USER_DIR"
sudo chmod 700 "$USER_DIR"

wg genkey | sudo tee "$USER_DIR/private.key" > /dev/null
sudo wg pubkey < "$USER_DIR/private.key" | sudo tee "$USER_DIR/public.key" > /dev/null
wg genpsk | sudo tee "$USER_DIR/preshared.key" > /dev/null
sudo chmod 600 "$USER_DIR/private.key" "$USER_DIR/preshared.key"

CLIENT_PRIVATE=$(sudo cat "$USER_DIR/private.key")
CLIENT_PUBLIC=$(sudo cat "$USER_DIR/public.key")
CLIENT_PSK=$(sudo cat "$USER_DIR/preshared.key")

# ── Créer le fichier de config client ─────────────────────────────────────
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

# ── Ajouter le peer dans wg0.conf ─────────────────────────────────────────
sudo tee -a "$WG_CONF" > /dev/null <<PEER

[Peer]
# Utilisateur: $USERNAME ($CLIENT_IP)
PublicKey = $CLIENT_PUBLIC
PresharedKey = $CLIENT_PSK
AllowedIPs = $CLIENT_IP/32
PEER

# ── Recharger WireGuard (sans couper les connexions actives) ───────────────
sudo wg addconf wg0 <(sudo wg-quick strip wg0 2>/dev/null || true) 2>/dev/null || \
  sudo systemctl reload wg-quick@wg0 2>/dev/null || \
  sudo wg set wg0 peer "$CLIENT_PUBLIC" preshared-key "$USER_DIR/preshared.key" allowed-ips "$CLIENT_IP/32"

echo -e "${GREEN}=== Utilisateur VPN '$USERNAME' créé ===${NC}"
echo "  IP VPN client : $CLIENT_IP"
echo "  Config client : $CLIENT_CONF"
echo ""

# ── Afficher QR code (pour mobile) ───────────────────────────────────────
if command -v qrencode &>/dev/null; then
  echo -e "${YELLOW}QR Code (importer dans l'app WireGuard sur mobile) :${NC}"
  sudo qrencode -t ansiutf8 < "$CLIENT_CONF"
  echo ""
fi

echo -e "${YELLOW}Config texte (pour import manuel sur Windows/Mac) :${NC}"
echo "Fichier : $CLIENT_CONF"
echo ""
sudo cat "$CLIENT_CONF"
echo ""
echo "Voir ops/VPN_GUIDE.md pour les instructions d'installation client."
