# Guide WireGuard VPN — Accès distant à Rubicon

Ce guide explique comment les employés nomades peuvent accéder à Odoo Rubicon depuis l'extérieur.

## Principe

WireGuard crée un tunnel chiffré entre votre appareil et le serveur Rubicon. Une fois connecté, vous accédez à Odoo comme si vous étiez sur le réseau interne de l'entreprise.

```
Votre PC/mobile  ──── WireGuard VPN ────  Serveur Rubicon  ──── Odoo
                     (chiffré, UDP 51820)   (10.8.0.1)      (http://10.8.0.1:8069)
```

## Pré-requis

Votre administrateur IT doit avoir exécuté `./ops/add_vpn_user.sh <votre_nom>` pour créer votre profil VPN.

---

## Installation — Windows

1. Télécharger WireGuard : https://www.wireguard.com/install/
2. Installer et lancer l'application
3. Cliquer **"Add Tunnel"** → **"Import tunnel(s) from file"**
4. Sélectionner le fichier `.conf` fourni par l'administrateur (ex: `jean_dupont.conf`)
5. Cliquer **"Activate"** pour se connecter

**Accès Odoo :** http://10.8.0.1:8069

---

## Installation — macOS

1. Télécharger WireGuard depuis l'App Store : chercher "WireGuard"
2. Ouvrir l'app → cliquer **"+"** → **"Add empty tunnel..."**
3. Coller le contenu du fichier `.conf` fourni, ou importer via **"Import tunnel(s) from file"**
4. Activer le tunnel

**Accès Odoo :** http://10.8.0.1:8069

---

## Installation — Android / iOS

1. Installer l'app WireGuard depuis Google Play ou App Store
2. Votre administrateur vous enverra un **QR code**
3. Dans l'app : toucher **"+"** → **"Scanner un QR code"**
4. Scanner le QR code
5. Activer le tunnel

**Accès Odoo :** http://10.8.0.1:8069

---

## Connexion

Une fois le tunnel activé :
- Ouvrir un navigateur
- Aller sur **http://10.8.0.1:8069**
- Se connecter avec vos identifiants Odoo habituels

---

## Dépannage

| Problème | Solution |
|----------|----------|
| Impossible de se connecter au tunnel | Vérifier que le port UDP 51820 n'est pas bloqué par votre réseau (Wi-Fi hôtel, etc.) |
| Odoo ne répond pas | Vérifier que le tunnel est bien actif (icône verte dans l'app) |
| Connexion lente | Normal sur une connexion mobile — le VPN ajoute une légère latence |
| QR code expiré | Contacter l'administrateur pour regénérer la config |

---

## Sécurité

- **Ne partagez jamais** votre fichier `.conf` ou QR code avec quelqu'un d'autre
- Si vous perdez votre appareil, contactez immédiatement l'administrateur pour révoquer votre accès
- Le VPN ne remplace pas votre mot de passe Odoo — utilisez un mot de passe fort

---

## Administration — Révoquer un accès

```bash
# Supprimer un utilisateur
USERNAME=jean_dupont
# 1. Récupérer la clé publique
CLIENT_PUBLIC=$(sudo cat /etc/wireguard/keys/users/$USERNAME/public.key)
# 2. Supprimer le peer actif
sudo wg set wg0 peer "$CLIENT_PUBLIC" remove
# 3. Supprimer le bloc [Peer] dans /etc/wireguard/wg0.conf manuellement
# 4. Supprimer les fichiers de clés
sudo rm -rf /etc/wireguard/keys/users/$USERNAME
```
