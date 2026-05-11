# Rubicon Demo — Deployment Guide

The demo runs as a separate Docker stack on port `8070`, fronté par un tunnel Cloudflare (HTTPS).
Il partage le même codebase que la production — aucun code n'est dupliqué.

---

## Prérequis

- Ubuntu 22.04 / Debian 12 VPS — minimum 2 vCPU, 2 GB RAM, 20 GB disk
- Docker + Docker Compose installés
- Accès SSH au serveur

---

## Première installation

### 1. Cloner le repo sur le serveur

```bash
git clone <repo-url> ~/rubicon-suite
cd ~/rubicon-suite
```

### 2. Créer le fichier de credentials

```bash
cp .env.demo.example .env.demo
nano .env.demo
```

Remplir les deux variables :
```bash
POSTGRES_PASSWORD=<mot_de_passe_db_fort>
DEMO_ADMIN_PASSWORD=<mot_de_passe_admin_odoo>
```

Pour générer des mots de passe forts :
```bash
python3 -c "import secrets, string; print(''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(24)))"
```

### 3. Démarrer le stack et initialiser la base

```bash
docker compose -f docker-compose.demo.yml up -d
sleep 8
docker compose -f docker-compose.demo.yml exec --user root odoo_demo \
  chown -R odoo:odoo /var/lib/odoo

# Initialisation (~3-5 min)
docker compose -f docker-compose.demo.yml run --rm odoo_demo odoo \
  -d rubicondemo \
  -i rubicon_demo,pdp_frontend,sis_frontend,rubicon_uom \
  --stop-after-init

docker compose -f docker-compose.demo.yml up -d
```

> Note : utiliser `run --rm` (pas `exec`) pour l'initialisation — évite le conflit de port si Odoo tourne déjà.

### 4. Sécuriser le serveur

```bash
# Génère admin_passwd, active list_db=False, proxy_mode=True
./ops/harden_demo.sh --restart

# Applique le mot de passe admin Odoo (depuis DEMO_ADMIN_PASSWORD dans .env.demo)
./ops/start_demo.sh

# Installe cloudflared comme service systemd → tunnel HTTPS *.trycloudflare.com
./ops/setup_cloudflare_tunnel.sh --service

# Ferme le port 8070 à l'extérieur (UFW)
./ops/setup_firewall.sh demo
```

**Si hébergé sur Oracle Cloud :** fermer aussi le port 8070 dans la console cloud :
Oracle Cloud Console → Networking → Virtual Cloud Networks → ton VCN → Security Lists → supprimer la règle ingress TCP 8070.

### 5. Récupérer l'URL HTTPS

```bash
sudo journalctl -u cloudflared-tunnel -n 50 --no-pager | grep -i trycloudflare
```

L'URL `https://xxx.trycloudflare.com` est ce que tu envoies aux clients.
**Attention :** elle change à chaque redémarrage du service cloudflared.

---

## Mise à jour du code

```bash
cd ~/rubicon-suite
git pull
docker compose -f docker-compose.demo.yml stop odoo_demo
docker compose -f docker-compose.demo.yml run --rm odoo_demo odoo \
  -d rubicondemo \
  -u rubicon_demo,pdp_frontend,sis_frontend,rubicon_uom \
  --stop-after-init
docker compose -f docker-compose.demo.yml up -d
```

---

## Reset complet (repartir de zéro)

À faire après un changement de données demo ou si la DB est dans un état incohérent.

```bash
git pull
docker compose -f docker-compose.demo.yml down -v
docker compose -f docker-compose.demo.yml up -d
sleep 8
docker compose -f docker-compose.demo.yml exec --user root odoo_demo \
  chown -R odoo:odoo /var/lib/odoo

docker compose -f docker-compose.demo.yml run --rm odoo_demo odoo \
  -d rubicondemo \
  -i rubicon_demo,pdp_frontend,sis_frontend,rubicon_uom \
  --stop-after-init

docker compose -f docker-compose.demo.yml up -d
./ops/start_demo.sh
```

---

## Vérifications

```bash
# Odoo répond en local
curl -s http://localhost:8070/web/health

# Port 8070 inaccessible depuis l'extérieur (doit timeout)
curl --max-time 5 http://<IP_VPS>:8070/web/health

# URL Cloudflare
sudo journalctl -u cloudflared-tunnel -n 50 --no-pager | grep -i trycloudflare
```

---

## En cas d'erreur filestore

Si l'initialisation échoue avec `FileNotFoundError` sur le filestore :

```bash
docker compose -f docker-compose.demo.yml down -v
# Reprendre depuis l'étape "Démarrer le stack" ci-dessus
```

---

## Arrêter la démo

```bash
# Arrêt simple (données conservées)
docker compose -f docker-compose.demo.yml down

# Arrêt + suppression de toutes les données
docker compose -f docker-compose.demo.yml down -v
```
