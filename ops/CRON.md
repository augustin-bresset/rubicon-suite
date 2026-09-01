# Cron Jobs — Rubicon Suite

## Setup

```bash
sudo crontab -e        # root: the backup scripts read the Docker volumes and .env.* files
```

Paste the lines corresponding to your environment. Adjust the repository path
(`/opt/rubicon` below) to where the code is checked out.

The backup script writes its full log to `$BACKUP_DIR/backup.log`
(`/opt/rubicon-backups/backup.log` by default) and prints a single summary
line, so set `MAILTO` to receive that line by mail on every run.

---

## Production Server

```cron
MAILTO=admin@company.com

# Daily backup at 02:00 (local + encrypted off-site copy on OCI)
0 2 * * * /opt/rubicon/ops/backup.sh prod

# Weekly restore test (Sunday 04:00): restores the latest backup into
# rubicon_verify, neutralizes it, checks row counts and filestore, drops it.
0 4 * * 0 /opt/rubicon/ops/verify_backup.sh prod > /dev/null

# Healthcheck every 5 minutes (log on failure)
*/5 * * * * /opt/rubicon/ops/healthcheck.sh prod >> /var/log/rubicon-health.log 2>&1 || \
  echo "$(date): HEALTHCHECK FAILED" >> /var/log/rubicon-health.log

# Let's Encrypt renewal is handled by the certbot systemd timer installed with
# python3-certbot-nginx (check: systemctl list-timers | grep certbot).
```

---

## Demo Server (Oracle Cloud VPS)

```cron
MAILTO=admin@company.com

# Daily backup at 02:00 (local only)
0 2 * * * /home/ubuntu/rubicon-suite/ops/backup.sh demo

# Weekly restore test (Sunday 04:00)
0 4 * * 0 /home/ubuntu/rubicon-suite/ops/verify_backup.sh demo > /dev/null

# Healthcheck every 5 minutes (log on failure)
*/5 * * * * /home/ubuntu/rubicon-suite/ops/healthcheck.sh demo >> /var/log/rubicon-health.log 2>&1 || \
  echo "$(date): HEALTHCHECK FAILED" >> /var/log/rubicon-health.log
```

---

## Verify Active Crons

```bash
sudo crontab -l
```

## Check Logs

```bash
tail -f /opt/rubicon-backups/backup.log     # backups
tail -f /opt/rubicon-backups/verify.log     # weekly restore tests
tail -f /var/log/rubicon-health.log         # healthchecks
```
