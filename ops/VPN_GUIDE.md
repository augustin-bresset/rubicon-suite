# WireGuard VPN Guide — Remote Access to Rubicon

This guide explains how remote employees can access Odoo Rubicon from outside the office.

## How it works

WireGuard creates an encrypted tunnel between your device and the Rubicon server. Once connected, you access Odoo as if you were on the company's internal network.

```
Your PC/mobile  ──── WireGuard VPN ────  Rubicon Server  ──── Odoo
                     (encrypted, UDP 51820)  (10.8.0.1)    (http://10.8.0.1:8069)
```

## Prerequisites

Your IT administrator must have run `./ops/add_vpn_user.sh <your_name>` to create your VPN profile.

---

## Installation — Windows

1. Download WireGuard: https://www.wireguard.com/install/
2. Install and launch the application
3. Click **"Add Tunnel"** → **"Import tunnel(s) from file"**
4. Select the `.conf` file provided by your administrator (e.g. `john_doe.conf`)
5. Click **"Activate"** to connect

**Odoo access:** http://10.8.0.1:8069

---

## Installation — macOS

1. Download WireGuard from the App Store: search "WireGuard"
2. Open the app → click **"+"** → **"Add empty tunnel..."**
3. Paste the contents of the `.conf` file provided, or import via **"Import tunnel(s) from file"**
4. Activate the tunnel

**Odoo access:** http://10.8.0.1:8069

---

## Installation — Android / iOS

1. Install the WireGuard app from Google Play or the App Store
2. Your administrator will send you a **QR code**
3. In the app: tap **"+"** → **"Scan a QR code"**
4. Scan the QR code
5. Activate the tunnel

**Odoo access:** http://10.8.0.1:8069

---

## Connecting

Once the tunnel is active:
- Open a browser
- Go to **http://10.8.0.1:8069**
- Log in with your usual Odoo credentials

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Cannot connect to the tunnel | Check that UDP port 51820 is not blocked by your network (hotel Wi-Fi, etc.) |
| Odoo not responding | Verify the tunnel is active (green icon in the app) |
| Slow connection | Normal on a mobile connection — VPN adds slight latency |
| QR code expired | Contact your administrator to regenerate the config |

---

## Security

- **Never share** your `.conf` file or QR code with anyone else
- If you lose your device, immediately contact your administrator to revoke your access
- The VPN does not replace your Odoo password — use a strong password

---

## Administration — Revoking Access

```bash
# Remove a user
USERNAME=john_doe
# 1. Get the public key
CLIENT_PUBLIC=$(sudo cat /etc/wireguard/keys/users/$USERNAME/public.key)
# 2. Remove the active peer
sudo wg set wg0 peer "$CLIENT_PUBLIC" remove
# 3. Manually remove the [Peer] block in /etc/wireguard/wg0.conf
# 4. Delete the key files
sudo rm -rf /etc/wireguard/keys/users/$USERNAME
```