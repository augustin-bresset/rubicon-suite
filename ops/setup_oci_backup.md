# Oracle Object Storage Setup for Off-site Backups

Step-by-step guide to connect `ops/backup.sh prod` to Oracle Cloud Object Storage.

What the script uploads: every backup file (`prod_db_*.sql.gz`,
`prod_filestore_*.tar.gz`, `prod_config_*.tar.gz`) **encrypted with `age`**, as
`prod/<tier>/<YYYYMMDD>/<file>.age`, plus the plaintext `SHA256SUMS`. The tier
is `monthly` on the 1st of the month, `weekly` on Sundays, `daily` otherwise.
Retention is enforced by a bucket lifecycle policy (step 6), not by the script.

---

## 1. Create the bucket

1. Log in to the Oracle Cloud console: https://cloud.oracle.com
2. Main menu → **Storage → Object Storage & Archive Storage → Buckets**
3. **Create Bucket**
   - **Bucket Name:** `rubicon-backups`
   - **Storage Tier:** Standard
   - **Visibility:** Private (never public)
   - **Versioning:** Disabled (backups are already timestamped)
   - **Emit Object Events:** off

---

## 2. Create an API key (dedicated backup user)

Use a dedicated IAM user (e.g. `rubicon-backup`) rather than an administrator
account, so a leaked key from the server can only touch this bucket.

1. **Identity & Security → Users → Create User** (`rubicon-backup`), then open it
2. **API keys → Add API Key → Generate API Key Pair** → download the private key (`.pem`)
3. Copy the configuration block displayed:

```ini
[DEFAULT]
user=ocid1.user.oc1..aaaa...
fingerprint=xx:xx:xx:xx:xx:xx:xx:xx:xx:xx:xx:xx:xx:xx:xx:xx
tenancy=ocid1.tenancy.oc1..aaaa...
region=eu-paris-1
key_file=~/.oci/oci_api_key.pem
```

4. **Identity & Security → Policies → Create Policy**, restricting the user to the bucket:

```
Allow user rubicon-backup to read buckets in compartment <compartment>
Allow user rubicon-backup to manage objects in compartment <compartment> where target.bucket.name='rubicon-backups'
```

---

## 3. Install the tools on the server

```bash
# OCI CLI
bash -c "$(curl -fsSL https://raw.githubusercontent.com/oracle/oci-cli/master/scripts/install/install.sh)"
# age (backup encryption)
sudo apt-get install -y age
```

---

## 4. Configure OCI CLI (as root, since the backup cron runs as root)

```bash
sudo mkdir -p /root/.oci && sudo chmod 700 /root/.oci
sudo cp /path/to/your_key.pem /root/.oci/oci_api_key.pem
sudo chmod 600 /root/.oci/oci_api_key.pem
sudo tee /root/.oci/config > /dev/null << 'CONF'
[DEFAULT]
user=ocid1.user.oc1..YOUR_USER_OCID
fingerprint=YOUR_FINGERPRINT
tenancy=ocid1.tenancy.oc1..YOUR_TENANCY_OCID
region=YOUR_REGION
key_file=/root/.oci/oci_api_key.pem
CONF
sudo chmod 600 /root/.oci/config
```

Test:

```bash
sudo oci os ns get                                    # -> { "data": "your_namespace" }
echo test | gzip | sudo oci os object put --bucket-name rubicon-backups --file - --name test/ping.gz
sudo oci os object list --bucket-name rubicon-backups
sudo oci os object delete --bucket-name rubicon-backups --object-name test/ping.gz --force
```

---

## 5. Encryption key

Generate the key pair **on a trusted workstation**, not on the server:

```bash
age-keygen -o rubicon-backup.key
# Public key: age1...
```

- Put the `age1...` public key in `.env.prod` as `BACKUP_AGE_RECIPIENT`.
- Store `rubicon-backup.key` (the private key) in the company password manager
  and on an offline medium. It is only needed to restore from OCI
  (`ops/restore.sh prod <date> --from-oci --identity rubicon-backup.key`).
  **Without it the off-site copies are unreadable for everyone.**
- The server itself never needs the private key: local backups stay in
  plaintext under `/opt/rubicon-backups` (root only) and the weekly restore
  test uses those.

Manual decryption, if ever needed:

```bash
age -d -i rubicon-backup.key -o prod_db_20260901_020000.sql.gz prod_db_20260901_020000.sql.gz.age
```

---

## 6. Retention: bucket lifecycle policy

Object Storage needs permission to act on your behalf (once per tenancy):

```
Allow service objectstorage-<region> to manage object-family in compartment <compartment>
```

Then apply the rules (daily 30 days, weekly 120 days, monthly 400 days):

```bash
sudo oci os object-lifecycle-policy put --bucket-name rubicon-backups --items '[
  {"name": "expire-daily",   "action": "DELETE", "isEnabled": true, "timeAmount": 30,  "timeUnit": "DAYS",
   "objectNameFilter": {"inclusionPrefixes": ["prod/daily/"]}},
  {"name": "expire-weekly",  "action": "DELETE", "isEnabled": true, "timeAmount": 120, "timeUnit": "DAYS",
   "objectNameFilter": {"inclusionPrefixes": ["prod/weekly/"]}},
  {"name": "expire-monthly", "action": "DELETE", "isEnabled": true, "timeAmount": 400, "timeUnit": "DAYS",
   "objectNameFilter": {"inclusionPrefixes": ["prod/monthly/"]}}
]'
sudo oci os object-lifecycle-policy get --bucket-name rubicon-backups
```

---

## 7. Run

```bash
sudo ./ops/backup.sh prod              # local + encrypted upload
sudo ./ops/backup.sh prod --no-oci     # local only (e.g. no network)
sudo tail -n 30 /opt/rubicon-backups/backup.log
```

The run is reported with warnings (exit code 2, status `WARN` for
`ops/healthcheck.sh`) when the upload is skipped because `age`, the OCI CLI or
`BACKUP_AGE_RECIPIENT` is missing — plaintext never leaves the host.

Restore from OCI on a fresh host (the config archive contains `.env.prod` and
`odoo.prod.conf`):

```bash
sudo ./ops/restore.sh prod latest --from-oci --identity /root/rubicon-backup.key
```

---

## Estimated Costs

Oracle Object Storage (Standard Tier): ~$0.0255/GB/month.
With a 2 GB backup per day: daily tier ≈ 60 GB, weekly ≈ 34 GB, monthly ≈ 26 GB
→ ~120 GB ≈ $3/month. Egress is free for the first 10 TB/month.
