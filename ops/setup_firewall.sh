#!/bin/bash
# Configure UFW (firewall) pour le serveur demo ou production.
# Usage: ./ops/setup_firewall.sh [demo|prod]
#   demo : ouvre 22, 80, 443 — ferme 8070 (Odoo via tunnel uniquement)
#   prod : ouvre 22 (interne), 51820/udp (WireGuard) — ferme tout le reste
#
# ATTENTION : nécessite sudo. Vérifie que SSH est bien autorisé avant d'activer.

set -e

MODE="${1:-demo}"
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

if ! command -v ufw &>/dev/null; then
  echo "Installation de ufw..."
  sudo apt-get install -y ufw
fi

echo -e "${YELLOW}=== Configuration firewall (mode: $MODE) ===${NC}"
echo ""
echo -e "${RED}ATTENTION: Vérifiez que votre session SSH restera active avant de continuer.${NC}"
echo "Ce script va activer UFW. Si SSH (port 22) n'est pas autorisé, vous perdrez l'accès."
echo ""
read -p "Continuer ? [y/N] " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
  echo "Annulé."
  exit 0
fi

# ── Règles communes ───────────────────────────────────────────────────────
sudo ufw --force reset
sudo ufw default deny incoming
sudo ufw default allow outgoing

# SSH toujours ouvert (évite lockout)
sudo ufw allow 22/tcp comment 'SSH'

if [ "$MODE" = "demo" ]; then
  # ── Mode demo (Oracle Cloud VPS) ────────────────────────────────────────
  # Port 80/443 pour futur Let's Encrypt ou nginx
  sudo ufw allow 80/tcp  comment 'HTTP (futur redirect HTTPS)'
  sudo ufw allow 443/tcp comment 'HTTPS (futur direct)'
  # Port 8070 intentionnellement FERMÉ
  # cloudflared se connecte en outbound (pas besoin d'inbound)
  echo ""
  echo "Règles demo appliquées :"
  echo "  ✓ 22/tcp   — SSH"
  echo "  ✓ 80/tcp   — HTTP (futur Let's Encrypt)"
  echo "  ✓ 443/tcp  — HTTPS"
  echo "  ✗ 8070     — FERMÉ (accès via Cloudflare Tunnel uniquement)"
  echo "  ✗ 5432     — FERMÉ (PostgreSQL interne uniquement)"

elif [ "$MODE" = "prod" ]; then
  # ── Mode production (serveur local entreprise) ───────────────────────────
  # 8069 uniquement depuis le réseau interne
  # Adapter 192.168.0.0/16 selon le sous-réseau réel de l'entreprise
  sudo ufw allow from 192.168.0.0/16 to any port 8069 proto tcp comment 'Odoo (réseau interne)'
  # WireGuard VPN (UDP)
  sudo ufw allow 51820/udp comment 'WireGuard VPN'
  echo ""
  echo "Règles production appliquées :"
  echo "  ✓ 22/tcp          — SSH (tout)"
  echo "  ✓ 8069/tcp        — Odoo (réseau 192.168.0.0/16 uniquement)"
  echo "  ✓ 51820/udp       — WireGuard VPN"
  echo "  ✗ tout le reste   — BLOQUÉ"
  echo ""
  echo -e "${YELLOW}Adapter le sous-réseau 192.168.0.0/16 si nécessaire.${NC}"

else
  echo "Mode inconnu: $MODE (utiliser 'demo' ou 'prod')"
  exit 1
fi

# ── Activer UFW ───────────────────────────────────────────────────────────
sudo ufw --force enable
echo ""
echo -e "${GREEN}UFW activé.${NC}"
echo ""
sudo ufw status verbose
echo ""
echo -e "${YELLOW}RAPPEL Oracle Cloud (mode demo) :${NC}"
echo "Dans la console Oracle Cloud → Networking → Security Lists :"
echo "  - Ouvrir : 22/tcp, 80/tcp, 443/tcp"
echo "  - Fermer : 8070/tcp, 5432/tcp"
echo "Voir ops/SECURITY.md pour les instructions détaillées."
