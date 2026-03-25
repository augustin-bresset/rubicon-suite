# Monitoring — Rubicon Suite

## UptimeRobot (externe, gratuit)

UptimeRobot surveille votre service depuis l'extérieur et envoie des alertes email si le service tombe.

### Configuration (demo)

1. Créer un compte sur https://uptimerobot.com (plan gratuit = 50 monitors, check toutes les 5 min)
2. Cliquer **"Add New Monitor"**
3. Paramètres :
   - **Monitor Type :** HTTP(s)
   - **Friendly Name :** Rubicon Demo
   - **URL :** `https://<votre-url>.trycloudflare.com/web/health`
   - **Monitoring Interval :** 5 minutes
4. **Alert Contacts :** ajouter votre email
5. Sauvegarder

UptimeRobot enverra un email si le service ne répond pas pendant > 5 minutes.

### Configuration (production avec VPN)

Pour la production (non exposée sur Internet), utiliser le healthcheck local + cron :

```bash
# Dans crontab -e :
*/5 * * * * /opt/rubicon/ops/healthcheck.sh prod > /tmp/rubicon_health_check.txt 2>&1 || \
  mail -s "ALERTE: Rubicon prod DOWN" admin@entreprise.com < /tmp/rubicon_health_check.txt
```

Prérequis : `apt install mailutils` + serveur SMTP configuré.

---

## Healthcheck local

```bash
# Vérification manuelle
./ops/healthcheck.sh demo
./ops/healthcheck.sh prod

# Voir les logs de healthcheck
tail -50 /var/log/rubicon-health.log
```

---

## Logs Odoo

```bash
# Logs en temps réel (demo)
docker compose -f docker-compose.demo.yml logs -f odoo_demo

# Logs en temps réel (prod)
docker compose logs -f odoo

# Dernières erreurs uniquement
docker compose -f docker-compose.demo.yml logs odoo_demo 2>&1 | grep -i "error\|critical\|traceback"
```

---

## Logs backup

```bash
tail -f /var/log/rubicon-backup.log
```

---

## Indicateurs à surveiller

| Indicateur | Seuil d'alerte | Commande |
|-----------|---------------|---------|
| Espace disque | > 80% | `df -h /` |
| Mémoire | > 90% | `free -h` |
| Backup absent | > 25h | voir `healthcheck.sh` |
| Containers down | toute panne | `docker compose ps` |
