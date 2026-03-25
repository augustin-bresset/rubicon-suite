#!/bin/bash
# Installe cloudflared et démarre un tunnel HTTPS anonyme vers Odoo demo.
# Usage: ./ops/setup_cloudflare_tunnel.sh [--service]
#   --service : installe cloudflared en service systemd persistant (redémarre au boot)
#
# Sans --service : lance le tunnel en foreground (pour tester).
# L'URL https://*.trycloudflare.com est affichée dans les logs.
#
# IMPORTANT : après installation, ajouter proxy_mode = True dans odoo_demo.conf
# puis redémarrer odoo_demo.

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
AS_SERVICE="${1:-}"

# ── Vérifications ──────────────────────────────────────────────────────────
if ! command -v curl &>/dev/null; then
  echo "Erreur: curl requis" && exit 1
fi

# ── Installation cloudflared ───────────────────────────────────────────────
if command -v cloudflared &>/dev/null; then
  echo "cloudflared déjà installé : $(cloudflared --version)"
else
  echo "Installation de cloudflared..."
  # Clé GPG Cloudflare
  curl -fsSL https://pkg.cloudflare.com/cloudflare-main.gpg \
    | sudo gpg --dearmor -o /usr/share/keyrings/cloudflare-main.gpg

  # Source APT
  echo "deb [signed-by=/usr/share/keyrings/cloudflare-main.gpg] \
https://pkg.cloudflare.com/cloudflared $(lsb_release -cs) main" \
    | sudo tee /etc/apt/sources.list.d/cloudflared.list > /dev/null

  sudo apt-get update -qq
  sudo apt-get install -y cloudflared
  echo "cloudflared installé : $(cloudflared --version)"
fi

# ── Mode service systemd ───────────────────────────────────────────────────
if [ "$AS_SERVICE" = "--service" ]; then
  echo ""
  echo "Installation du service systemd cloudflared..."
  echo "Le tunnel sera lancé automatiquement au démarrage du serveur."
  echo ""

  # Créer le fichier de service
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
  echo "Service démarré. Attente de l'URL du tunnel..."
  sleep 8
  echo ""
  echo "URL du tunnel (chercher 'trycloudflare.com' dans les logs) :"
  sudo journalctl -u cloudflared-tunnel -n 30 --no-pager | grep -i "trycloudflare\|https://" || true
  echo ""
  echo "Pour voir les logs en direct :"
  echo "  sudo journalctl -u cloudflared-tunnel -f"
  echo ""
  echo "RAPPEL : ajouter 'proxy_mode = True' dans odoo_conf/odoo_demo.conf"
  echo "puis : docker compose -f docker-compose.demo.yml restart odoo_demo"

else
  # ── Mode foreground (test) ─────────────────────────────────────────────
  echo ""
  echo "Lancement du tunnel en foreground (Ctrl+C pour arrêter)..."
  echo "L'URL https://*.trycloudflare.com apparaîtra dans quelques secondes."
  echo ""
  cloudflared tunnel --url http://localhost:8070 --no-autoupdate
fi
