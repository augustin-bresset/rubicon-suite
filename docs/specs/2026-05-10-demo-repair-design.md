# Demo Repair & Hardening — Design Spec

**Date:** 2026-05-10  
**Approach chosen:** C — Reset propre + sécurisation + données demo enrichies

---

## Context

The demo instance hosted at `89.168.58.215:8070` is broken (most OWL views fail to render). The code on the server is up to date (`git pull` done), but the Odoo modules were not updated after the pull and the DB may be in an inconsistent state. The instance runs over plain HTTP with no reverse proxy, making it unsuitable for external clients who connect themselves.

---

## Section 1 — Demo Data Enrichment

The `rubicon_demo` module XML (`rubicon_addons/rubicon_demo/data/rubicon_demo_data.xml`) already covers the core PDP and SIS data. The following will be added before the reset:

### 1.1 Footnotes on SIS documents
Add a `footnotes` field to 2–3 demo documents (one quotation, one order, one invoice) so clients can see the footnote feature in action.

### 1.2 Document names in autonumber format
Current demo document names (`DEMO-Q-001`, `DEMO-O-001`) don't match the autonumber format (`SQ-SJC-26001`). Replace with correctly formatted names so the demo looks consistent with real usage. Format: `{doc_type_code}-{party_sis_code}-{YY}{sequence}`.

Example replacements:
- `DEMO-Q-001` → `SQ-SJC-26001` (Siam Jewels, quotation)
- `DEMO-Q-002` → `SQ-TFJ-26001` (Tokyo Fine Jewelry)
- `DEMO-Q-003` → `SQ-MDO-26001` (Maison Dorée)
- `DEMO-O-001` → `SO-SJC-26001`
- `DEMO-O-002` → `SO-GPT-26001`
- `DEMO-O-003` → `SO-MGI-26001`
- `DEMO-I-001` → `SI-TFJ-26001`
- `DEMO-I-002` → `SI-SJC-26001`
- `DEMO-I-003` → `SI-MDO-26001`

### 1.3 PDP currency settings
Add a few `pdp.currency.setting` records (USD active, EUR active) so the currency tab in the PDP workspace is not empty.

### 1.4 Products marked in_collection
Mark 2–3 products as `in_collection = True` to demonstrate the collection filter in the PDP workspace.

---

## Section 2 — Deployment Sequence

All commands run on the VPS over SSH. The repo is already cloned at `/opt/rubicon-demo` (or equivalent path on server).

1. **Enrich demo data locally** → `git push` → `git pull` on server
2. **Stop and wipe the demo stack:**
   ```bash
   docker compose -f docker-compose.demo.yml down -v
   ```
3. **Start the stack and fix filestore permissions:**
   ```bash
   docker compose -f docker-compose.demo.yml up -d
   sleep 8
   docker compose -f docker-compose.demo.yml exec --user root odoo_demo \
     chown -R odoo:odoo /var/lib/odoo
   ```
4. **Initialize the database:**
   ```bash
   docker compose -f docker-compose.demo.yml exec odoo_demo odoo \
     -d rubicondemo \
     -i rubicon_demo,pdp_frontend,sis_frontend,rubicon_uom \
     --stop-after-init
   ```
5. **Restart Odoo in normal mode:**
   ```bash
   docker compose -f docker-compose.demo.yml up -d
   ```

---

## Section 3 — Security Hardening

All scripts are in `ops/` and already exist in the repo.

### 3.1 Admin password
Set `DEMO_ADMIN_PASSWORD` to a strong value in `.env.demo` on the server before running any scripts. `start_demo.sh` applies it automatically.

### 3.2 harden_demo.sh
Run `./ops/harden_demo.sh --restart` after initialization. This:
- Generates a strong `admin_passwd` (protects `/web/database/manager`)
- Sets `list_db = False` (hides the DB list)
- Sets `proxy_mode = True` (required for Cloudflare tunnel)
- Applies Odoo worker/memory limits

### 3.3 Cloudflare Tunnel
Run `./ops/setup_cloudflare_tunnel.sh --service` to install `cloudflared` as a systemd service. This creates a persistent `https://*.trycloudflare.com` URL.

**Note:** The URL changes on each service restart (anonymous tunnel). Retrieve it with:
```bash
sudo journalctl -u cloudflared-tunnel | grep trycloudflare
```

### 3.4 Firewall
Run `./ops/setup_firewall.sh` to close port 8070 to external traffic. Clients can only reach Odoo through the Cloudflare HTTPS URL.

### 3.5 Access
Clients receive the `https://xxx.trycloudflare.com` URL and log in with `admin` / `DEMO_ADMIN_PASSWORD`.

---

## Out of Scope

- Custom domain / Let's Encrypt (no domain available)
- Read-only demo user (admin access is sufficient for guided demos)
- Automated data reset on a schedule
