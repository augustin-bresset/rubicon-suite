# Configuration Oracle Object Storage pour les backups

Guide étape par étape pour connecter le script `ops/backup.sh` à Oracle Cloud Object Storage.

---

## 1. Créer le bucket dans Oracle Cloud

1. Se connecter à la console Oracle Cloud : https://cloud.oracle.com
2. Menu principal → **Storage → Object Storage & Archive Storage → Buckets**
3. Cliquer **"Create Bucket"**
   - **Bucket Name :** `rubicon-backups`
   - **Storage Tier :** Standard
   - **Versioning :** Disabled (les backups sont déjà horodatés)
4. Cliquer **"Create"**

---

## 2. Créer une clé API

1. Menu haut-droit → votre profil → **"My Profile"**
2. Scrollez jusqu'à **"API keys"** → **"Add API Key"**
3. Choisir **"Generate API Key Pair"** → Télécharger la clé privée (`.pem`)
4. Cliquer **"Add"**
5. **Copier le bloc de configuration** affiché (il ressemble à ceci) :

```ini
[DEFAULT]
user=ocid1.user.oc1..aaaa...
fingerprint=xx:xx:xx:xx:xx:xx:xx:xx:xx:xx:xx:xx:xx:xx:xx:xx
tenancy=ocid1.tenancy.oc1..aaaa...
region=eu-paris-1
key_file=~/.oci/oci_api_key.pem
```

---

## 3. Installer OCI CLI

```bash
# Python requis
pip3 install oci-cli

# Ou via le script officiel
bash -c "$(curl -fsSL https://raw.githubusercontent.com/oracle/oci-cli/master/scripts/install/install.sh)"
```

---

## 4. Configurer OCI CLI

```bash
# Créer le répertoire de config
mkdir -p ~/.oci
chmod 700 ~/.oci

# Copier votre clé privée téléchargée à l'étape 2
cp /chemin/vers/votre_cle.pem ~/.oci/oci_api_key.pem
chmod 600 ~/.oci/oci_api_key.pem

# Créer le fichier de config (coller le bloc de l'étape 2)
cat > ~/.oci/config << 'EOF'
[DEFAULT]
user=ocid1.user.oc1..VOTRE_OCID_USER
fingerprint=VOTRE_FINGERPRINT
tenancy=ocid1.tenancy.oc1..VOTRE_OCID_TENANCY
region=VOTRE_REGION
key_file=~/.oci/oci_api_key.pem
EOF
chmod 600 ~/.oci/config
```

---

## 5. Tester la connexion

```bash
# Vérifier la connexion
oci os ns get

# Doit retourner quelque chose comme :
# { "data": "votre_namespace" }

# Lister les buckets
oci os bucket list --compartment-id $(oci iam compartment list --query "data[0].id" --raw-output)

# Tester l'upload
echo "test" | gzip > /tmp/test_backup.gz
oci os object put --bucket-name rubicon-backups --file /tmp/test_backup.gz --name test/test_backup.gz
oci os object list --bucket-name rubicon-backups
oci os object delete --bucket-name rubicon-backups --object-name test/test_backup.gz --force
rm /tmp/test_backup.gz
echo "OCI Object Storage configuré avec succès."
```

---

## 6. Configurer les permissions IAM (optionnel, sécurité renforcée)

Pour limiter les droits de la clé API aux seules opérations de backup (lecture/écriture sur le bucket uniquement) :

1. Console Oracle Cloud → **Identity & Security → Policies**
2. Créer une policy :
   ```
   Allow user <votre_user> to manage objects in compartment <compartment> where target.bucket.name='rubicon-backups'
   ```

---

## 7. Utiliser le backup avec OCI

```bash
# Backup production avec upload OCI
./ops/backup.sh prod

# Backup sans OCI (si connexion indisponible)
./ops/backup.sh prod --no-oci
```

---

## Coûts estimés

Oracle Object Storage (Standard Tier) :
- **Stockage :** ~0.02$/GB/mois
- Pour 30 jours de backups production (estimation 2 GB/jour) : ~1.2$/mois
- **Sortie réseau :** gratuite pour les premières 10 TB/mois
