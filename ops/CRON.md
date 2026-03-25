# Cron Jobs — Rubicon Suite

## Setup

```bash
crontab -e
```

Paste the lines corresponding to your environment.

---

## Demo Server (Oracle Cloud VPS)

```cron
# Daily backup at 02:00
0 2 * * * /home/ubuntu/rubicon-suite/ops/backup.sh demo >> /var/log/rubicon-backup.log 2>&1

# Healthcheck every 5 minutes (log on failure)
*/5 * * * * /home/ubuntu/rubicon-suite/ops/healthcheck.sh demo >> /var/log/rubicon-health.log 2>&1 || \
  echo "$(date): HEALTHCHECK FAILED" >> /var/log/rubicon-health.log
```

---

## Production Server (On-premises)

```cron
# Daily backup at 02:00 (with OCI upload)
0 2 * * * /opt/rubicon/ops/backup.sh prod >> /var/log/rubicon-backup.log 2>&1

# Healthcheck every 5 minutes
*/5 * * * * /opt/rubicon/ops/healthcheck.sh prod >> /var/log/rubicon-health.log 2>&1 || \
  echo "$(date): HEALTHCHECK FAILED" >> /var/log/rubicon-health.log

# Let's Encrypt renewal (if future domain + nginx)
# 0 3 * * * certbot renew --quiet
```

---

## Verify Active Crons

```bash
crontab -l
```

## Check Logs

```bash
tail -f /var/log/rubicon-backup.log
tail -f /var/log/rubicon-health.log
```
