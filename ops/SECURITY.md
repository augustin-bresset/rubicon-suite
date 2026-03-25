# Sécurité — Rubicon Suite

## Vue d'ensemble des environnements

| Env | Accès | HTTPS | Firewall |
|-----|-------|-------|---------|
| Dev (localhost:8069) | Local uniquement | Non (inutile) | UFW désactivé |
| Demo (Oracle Cloud :8070) | Internet via Cloudflare Tunnel | Oui (Cloudflare) | UFW + Oracle Security List |
| Prod (local entreprise :8069) | Réseau interne + WireGuard VPN | Optionnel | UFW (réseau interne seulement) |

---

## Demo — Cloudflare Tunnel

Le port 8070 n'est **jamais** accessible directement depuis Internet.
Cloudflare Tunnel crée une connexion **sortante** du VPS vers Cloudflare.

```
Internet → Cloudflare → tunnel → localhost:8070
```

Pour installer/redémarrer le tunnel :
```bash
./ops/setup_cloudflare_tunnel.sh --service
```

---

## Demo — Oracle Cloud Security List

Dans la console Oracle Cloud → **Networking → Virtual Cloud Networks → Security Lists** :

### Ingress Rules (à conserver)
| Source CIDR | Protocol | Port | Commentaire |
|-------------|----------|------|-------------|
| 0.0.0.0/0 | TCP | 22 | SSH |
| 0.0.0.0/0 | TCP | 80 | HTTP (futur redirect HTTPS) |
| 0.0.0.0/0 | TCP | 443 | HTTPS (futur) |

### Ingress Rules (à supprimer/bloquer)
| Port | Action |
|------|--------|
| 8070 | Supprimer la règle |
| 5432 | Supprimer la règle (PostgreSQL) |

**Note :** Cloudflare Tunnel utilise uniquement des connexions **sortantes** — aucun port entrant n'est nécessaire pour le fonctionnement du tunnel.

---

## Demo — Durcissement Odoo

Exécuter une seule fois (ou après chaque réinstallation) :
```bash
./ops/harden_demo.sh --restart
```

Ce script configure :
- `admin_passwd` fort (48 chars) — protège `/web/database/manager`
- `list_db = False` — cache la liste et l'accès aux bases
- `workers = 2` — isolation entre requêtes
- Limites CPU/mémoire — protection contre les requêtes abusives

---

## Production — WireGuard VPN

Les employés nomades se connectent via WireGuard (UDP 51820).
Le port 8069 n'est accessible que depuis le réseau interne (192.168.x.x) ou via le VPN (10.8.x.x).

```bash
# Installer WireGuard
./ops/setup_wireguard.sh

# Ajouter un utilisateur
./ops/add_vpn_user.sh prenom_nom

# Guide employé
cat ops/VPN_GUIDE.md
```

---

## Checklist de sécurité

### Demo (à faire une fois)
- [ ] `./ops/harden_demo.sh --restart` exécuté
- [ ] `./ops/setup_cloudflare_tunnel.sh --service` actif
- [ ] `./ops/setup_firewall.sh demo` actif
- [ ] Oracle Cloud Security List : port 8070 fermé
- [ ] `DEMO_ADMIN_PASSWORD` défini dans `.env.demo` (≠ `CHANGE_ME`)
- [ ] Backup cron configuré (voir `ops/CRON.md`)
- [ ] UptimeRobot configuré (voir `ops/MONITORING.md`)

### Production (à faire avant mise en service)
- [ ] `./ops/setup_wireguard.sh` exécuté
- [ ] `./ops/setup_firewall.sh prod` actif
- [ ] `odoo.conf` avec `admin_passwd` fort et `list_db = False`
- [ ] Backup cron configuré + OCI testé
- [ ] `./ops/healthcheck.sh prod` passe sans erreur
- [ ] Au moins 1 backup de test restauré avec `./ops/restore.sh`

---

## Secrets et fichiers sensibles

Ces fichiers ne doivent **jamais** être commités dans git (vérifiés par .gitignore) :
- `.env` — credentials production
- `.env.demo` — credentials demo
- `.demo_secrets` — admin_passwd généré par harden_demo.sh
- `odoo_conf/odoo_demo.conf` — config demo avec admin_passwd
- `/etc/wireguard/` — clés WireGuard (sur le serveur uniquement)
