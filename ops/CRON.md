# Tâches cron — Rubicon Suite

## Installation

```bash
crontab -e
```

Coller les lignes correspondant à votre environnement.

---

## Serveur Demo (Oracle Cloud VPS)

```cron
# Backup quotidien à 02h00
0 2 * * * /home/ubuntu/rubicon-suite/ops/backup.sh demo >> /var/log/rubicon-backup.log 2>&1

# Healthcheck toutes les 5 minutes (log si erreur)
*/5 * * * * /home/ubuntu/rubicon-suite/ops/healthcheck.sh demo >> /var/log/rubicon-health.log 2>&1 || \
  echo "$(date): HEALTHCHECK FAILED" >> /var/log/rubicon-health.log
```

---

## Serveur Production (Local entreprise)

```cron
# Backup quotidien à 02h00 (avec upload OCI)
0 2 * * * /opt/rubicon/ops/backup.sh prod >> /var/log/rubicon-backup.log 2>&1

# Healthcheck toutes les 5 minutes
*/5 * * * * /opt/rubicon/ops/healthcheck.sh prod >> /var/log/rubicon-health.log 2>&1 || \
  echo "$(date): HEALTHCHECK FAILED" >> /var/log/rubicon-health.log

# Renouvellement Let's Encrypt (si futur domaine + nginx)
# 0 3 * * * certbot renew --quiet
```

---

## Vérifier les crons actifs

```bash
crontab -l
```

## Vérifier les logs

```bash
tail -f /var/log/rubicon-backup.log
tail -f /var/log/rubicon-health.log
```
