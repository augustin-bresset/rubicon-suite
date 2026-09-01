#!/bin/bash
# Baseline hardening of an Internet-facing Ubuntu/Debian host before it runs
# the production stack. Idempotent; re-run after OS upgrades.
#
# Usage: ./ops/server/harden_server.sh
#
#   1. SSH: key-only login, no root password login, 3 attempts
#      (drop-in /etc/ssh/sshd_config.d/60-rubicon.conf, validated with sshd -t)
#   2. fail2ban: sshd jail, plus the nginx-limit-req jail when nginx is present
#      (bans IPs that keep hitting the /web/login rate limit of nginx_prod.conf)
#   3. unattended-upgrades: automatic security updates
#   4. packages the ops scripts rely on: age, curl, ufw
#
# Refuses to disable password login when the current user has no authorized
# SSH key, so you cannot lock yourself out. Run ./ops/server/setup_firewall.sh
# online afterwards.

set -euo pipefail

GREEN='\033[0;32m'; RED='\033[0;31m'; YELLOW='\033[1;33m'; NC='\033[0m'
[ "$(id -u)" -eq 0 ] && SUDO="" || SUDO="sudo"

echo -e "${GREEN}=== Host hardening ===${NC}"

# ── 0. Lock-out guard ──────────────────────────────────────────────────────
KEYS="${HOME}/.ssh/authorized_keys"
if [ ! -s "$KEYS" ]; then
  echo -e "${RED}No SSH key in $KEYS for $(whoami). Add your public key first, then re-run.${NC}"
  exit 1
fi

# ── 1. Packages ────────────────────────────────────────────────────────────
export DEBIAN_FRONTEND=noninteractive
$SUDO apt-get update -qq
$SUDO apt-get install -y -qq fail2ban unattended-upgrades ufw age curl >/dev/null

# ── 2. SSH ─────────────────────────────────────────────────────────────────
$SUDO mkdir -p /etc/ssh/sshd_config.d
$SUDO tee /etc/ssh/sshd_config.d/60-rubicon.conf >/dev/null <<'CONF'
# Managed by ops/server/harden_server.sh
PasswordAuthentication no
KbdInteractiveAuthentication no
PermitRootLogin prohibit-password
PubkeyAuthentication yes
MaxAuthTries 3
X11Forwarding no
AllowTcpForwarding yes
ClientAliveInterval 300
ClientAliveCountMax 2
CONF
if $SUDO sshd -t; then
  $SUDO systemctl reload ssh 2>/dev/null || $SUDO systemctl reload sshd
  echo "SSH: key-only login enforced (60-rubicon.conf)"
else
  $SUDO rm -f /etc/ssh/sshd_config.d/60-rubicon.conf
  echo -e "${RED}sshd rejected the configuration — drop-in removed, nothing changed.${NC}"
  exit 1
fi

# ── 3. fail2ban ────────────────────────────────────────────────────────────
JAIL="/etc/fail2ban/jail.d/rubicon.local"
{
  echo "# Managed by ops/server/harden_server.sh"
  echo "[DEFAULT]"
  echo "bantime  = 1h"
  echo "findtime = 10m"
  echo "maxretry = 5"
  echo ""
  echo "[sshd]"
  echo "enabled = true"
  if command -v nginx >/dev/null 2>&1; then
    echo ""
    echo "[nginx-limit-req]"
    echo "enabled  = true"
    echo "logpath  = /var/log/nginx/rubicon.error.log"
    echo "maxretry = 10"
  fi
} | $SUDO tee "$JAIL" >/dev/null
$SUDO systemctl enable --now fail2ban >/dev/null
$SUDO systemctl restart fail2ban
echo "fail2ban: $(grep -c 'enabled' "$JAIL") jail(s) enabled"

# ── 4. Automatic security updates ─────────────────────────────────────────
$SUDO tee /etc/apt/apt.conf.d/20auto-upgrades >/dev/null <<'CONF'
APT::Periodic::Update-Package-Lists "1";
APT::Periodic::Unattended-Upgrade "1";
APT::Periodic::AutocleanInterval "7";
CONF
$SUDO systemctl enable --now unattended-upgrades >/dev/null 2>&1 || true
echo "unattended-upgrades: enabled"

echo ""
echo -e "${GREEN}=== Done ===${NC}"
echo -e "${YELLOW}Keep this SSH session open and test a new login from another terminal before logging out.${NC}"
echo "Next: ./ops/server/setup_firewall.sh online"
