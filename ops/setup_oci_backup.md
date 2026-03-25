# Oracle Object Storage Setup for Backups

Step-by-step guide to connect `ops/backup.sh` to Oracle Cloud Object Storage.

---

## 1. Create the bucket in Oracle Cloud

1. Log in to the Oracle Cloud console: https://cloud.oracle.com
2. Main menu → **Storage → Object Storage & Archive Storage → Buckets**
3. Click **"Create Bucket"**
   - **Bucket Name:** `rubicon-backups`
   - **Storage Tier:** Standard
   - **Versioning:** Disabled (backups are already timestamped)
4. Click **"Create"**

---

## 2. Create an API key

1. Top-right menu → your profile → **"My Profile"**
2. Scroll to **"API keys"** → **"Add API Key"**
3. Choose **"Generate API Key Pair"** → Download the private key (`.pem`)
4. Click **"Add"**
5. **Copy the configuration block** displayed (it looks like this):

```ini
[DEFAULT]
user=ocid1.user.oc1..aaaa...
fingerprint=xx:xx:xx:xx:xx:xx:xx:xx:xx:xx:xx:xx:xx:xx:xx:xx
tenancy=ocid1.tenancy.oc1..aaaa...
region=eu-paris-1
key_file=~/.oci/oci_api_key.pem
```

---

## 3. Install OCI CLI

```bash
# Python required
pip3 install oci-cli

# Or via the official installer
bash -c "$(curl -fsSL https://raw.githubusercontent.com/oracle/oci-cli/master/scripts/install/install.sh)"
```

---

## 4. Configure OCI CLI

```bash
# Create the config directory
mkdir -p ~/.oci
chmod 700 ~/.oci

# Copy your private key downloaded in step 2
cp /path/to/your_key.pem ~/.oci/oci_api_key.pem
chmod 600 ~/.oci/oci_api_key.pem

# Create the config file (paste the block from step 2)
cat > ~/.oci/config << 'EOF'
[DEFAULT]
user=ocid1.user.oc1..YOUR_USER_OCID
fingerprint=YOUR_FINGERPRINT
tenancy=ocid1.tenancy.oc1..YOUR_TENANCY_OCID
region=YOUR_REGION
key_file=~/.oci/oci_api_key.pem
EOF
chmod 600 ~/.oci/config
```

---

## 5. Test the connection

```bash
# Verify the connection
oci os ns get
# Should return something like:
# { "data": "your_namespace" }

# List buckets
oci os bucket list --compartment-id $(oci iam compartment list --query "data[0].id" --raw-output)

# Test upload
echo "test" | gzip > /tmp/test_backup.gz
oci os object put --bucket-name rubicon-backups --file /tmp/test_backup.gz --name test/test_backup.gz
oci os object list --bucket-name rubicon-backups
oci os object delete --bucket-name rubicon-backups --object-name test/test_backup.gz --force
rm /tmp/test_backup.gz
echo "OCI Object Storage configured successfully."
```

---

## 6. Configure IAM permissions (optional, enhanced security)

To restrict the API key to backup-only operations (read/write on the bucket only):

1. Oracle Cloud console → **Identity & Security → Policies**
2. Create a policy:
   ```
   Allow user <your_user> to manage objects in compartment <compartment> where target.bucket.name='rubicon-backups'
   ```

---

## 7. Use backup with OCI

```bash
# Production backup with OCI upload
./ops/backup.sh prod

# Backup without OCI (if connection unavailable)
./ops/backup.sh prod --no-oci
```

---

## Estimated Costs

Oracle Object Storage (Standard Tier):
- **Storage:** ~$0.02/GB/month
- For 30 days of production backups (estimate 2 GB/day): ~$1.20/month
- **Egress:** free for the first 10 TB/month
