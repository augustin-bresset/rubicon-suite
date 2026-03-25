# Monitoring — Rubicon Suite

## UptimeRobot (external, free)

UptimeRobot monitors your service from the outside and sends email alerts if the service goes down.

### Setup (demo)

1. Create an account at https://uptimerobot.com (free plan = 50 monitors, checks every 5 min)
2. Click **"Add New Monitor"**
3. Settings:
   - **Monitor Type:** HTTP(s)
   - **Friendly Name:** Rubicon Demo
   - **URL:** `https://<your-url>.trycloudflare.com/web/health`
   - **Monitoring Interval:** 5 minutes
4. **Alert Contacts:** add your email
5. Save

UptimeRobot will send an email if the service does not respond for > 5 minutes.

### Setup (production with VPN)

For production (not exposed to the Internet), use local healthcheck + cron:

```bash
# In crontab -e:
*/5 * * * * /opt/rubicon/ops/healthcheck.sh prod > /tmp/rubicon_health_check.txt 2>&1 || \
  mail -s "ALERT: Rubicon prod DOWN" admin@company.com < /tmp/rubicon_health_check.txt
```

Prerequisites: `apt install mailutils` + configured SMTP server.

---

## Local Healthcheck

```bash
# Manual check
./ops/healthcheck.sh demo
./ops/healthcheck.sh prod

# View healthcheck logs
tail -50 /var/log/rubicon-health.log
```

---

## Odoo Logs

```bash
# Live logs (demo)
docker compose -f docker-compose.demo.yml logs -f odoo_demo

# Live logs (prod)
docker compose logs -f odoo

# Errors only
docker compose -f docker-compose.demo.yml logs odoo_demo 2>&1 | grep -i "error\|critical\|traceback"
```

---

## Backup Logs

```bash
tail -f /var/log/rubicon-backup.log
```

---

## Metrics to Watch

| Metric | Alert threshold | Command |
|--------|----------------|---------|
| Disk space | > 80% used | `df -h /` |
| Memory | > 90% used | `free -h` |
| Missing backup | > 25h | see `healthcheck.sh` |
| Containers down | any outage | `docker compose ps` |
