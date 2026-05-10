# Demo Repair & Hardening Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Repair the broken demo instance, enrich the demo data XML, and secure the server with Cloudflare Tunnel + firewall so external clients can safely connect over HTTPS.

**Architecture:** Three sequential phases — (1) enrich demo data locally and push, (2) reset and reinitialize the DB on the VPS, (3) run the existing security scripts (`harden_demo.sh`, `setup_cloudflare_tunnel.sh`, `setup_firewall.sh`). All server scripts already exist in `ops/`; no new scripts need to be written.

**Tech Stack:** Odoo 18, Docker Compose, cloudflared (Cloudflare Tunnel), UFW firewall, bash.

---

## Files

| File | Change |
|------|--------|
| `rubicon_addons/rubicon_demo/data/rubicon_demo_data.xml` | Rename documents to autonumber format, add footnotes, add currency settings, mark products in_collection |
| `.env.demo.example` | Add `DEMO_ADMIN_PASSWORD=CHANGE_ME` line (missing from template) |

All other changes are server-side commands, not code.

---

## Task 1: Enrich the demo data XML — document names

Rename all SIS document `name` fields to match the real autonumber format (`{DOC_TYPE}-{CLIENT_CODE}-{YY}{SEQ:03d}`). This makes the demo look consistent with real usage.

**Files:**
- Modify: `rubicon_addons/rubicon_demo/data/rubicon_demo_data.xml`

- [ ] **Step 1: Rename document names in the XML**

In `rubicon_demo_data.xml`, find the 9 `sis.document` records (section 19) and replace their `name` fields:

```xml
<!-- demo_doc_quot -->
<field name="name">SQ-SJC-26001</field>

<!-- demo_doc_quot2 -->
<field name="name">SQ-TFJ-26001</field>

<!-- demo_doc_quot3 -->
<field name="name">SQ-MDO-26001</field>

<!-- demo_doc_order -->
<field name="name">SO-SJC-26001</field>

<!-- demo_doc_order2 -->
<field name="name">SO-GPT-26001</field>

<!-- demo_doc_order3 -->
<field name="name">SO-MGI-26001</field>

<!-- demo_doc_invoice -->
<field name="name">SI-TFJ-26001</field>

<!-- demo_doc_invoice2 -->
<field name="name">SI-SJC-26001</field>

<!-- demo_doc_invoice3 -->
<field name="name">SI-MDO-26001</field>
```

Do NOT change the `doc_type_code` field on any record — it stays as `SQ`, `SO`, or `SI`.

---

## Task 2: Add footnotes to 3 demo documents

Show the footnotes feature on one quotation, one order, and one invoice.

**Files:**
- Modify: `rubicon_addons/rubicon_demo/data/rubicon_demo_data.xml`

- [ ] **Step 1: Add `footnotes` field to `demo_doc_quot` (SQ-SJC-26001)**

Inside the `<record id="demo_doc_quot" ...>` block, add after the `notes` field:

```xml
<field name="footnotes">All prices are in USD. Valid for 30 days from the date of issue. Prices are subject to change based on metal market fluctuations.</field>
```

- [ ] **Step 2: Add `footnotes` to `demo_doc_order` (SO-SJC-26001)**

Inside the `<record id="demo_doc_order" ...>` block, add:

```xml
<field name="footnotes">Delivery timeline: 8–10 weeks after order confirmation and receipt of deposit. Rush orders available on request.</field>
```

- [ ] **Step 3: Add `footnotes` to `demo_doc_invoice` (SI-TFJ-26001)**

Inside the `<record id="demo_doc_invoice" ...>` block, add:

```xml
<field name="footnotes">Payment due within 60 days of invoice date. Late payments are subject to a 1.5% monthly fee. Bank wire details available on request.</field>
```

---

## Task 3: Add PDP currency settings

The PDP workspace has a currency tab backed by `pdp.currency.setting`. Without records it is empty. Add USD (base) and EUR.

**Files:**
- Modify: `rubicon_addons/rubicon_demo/data/rubicon_demo_data.xml`

- [ ] **Step 1: Add a new section 21 at the end of the XML (before `</odoo>`)**

```xml
    <!-- =========================================================
         21. PDP CURRENCY SETTINGS
         ========================================================= -->

    <record id="demo_currency_usd" model="pdp.currency.setting">
        <field name="currency_id" ref="base.USD"/>
        <field name="rate">1.0</field>
        <field name="sequence">1</field>
    </record>

    <record id="demo_currency_eur" model="pdp.currency.setting">
        <field name="currency_id" ref="base.EUR"/>
        <field name="rate">0.92</field>
        <field name="sequence">2</field>
    </record>

    <record id="demo_currency_hkd" model="pdp.currency.setting">
        <field name="currency_id" ref="base.HKD"/>
        <field name="rate">7.82</field>
        <field name="sequence">3</field>
    </record>
```

---

## Task 4: Mark products as in_collection

Flag 3 products so the collection filter in the PDP workspace is not empty.

**Files:**
- Modify: `rubicon_addons/rubicon_demo/data/rubicon_demo_data.xml`

- [ ] **Step 1: Add `in_collection` to 3 products**

In the `<record id="demo_prod_r01_dts" ...>` block, add:
```xml
<field name="in_collection" eval="True"/>
```

In the `<record id="demo_prod_e01_dts" ...>` block, add:
```xml
<field name="in_collection" eval="True"/>
```

In the `<record id="demo_prod_p01_dts" ...>` block, add:
```xml
<field name="in_collection" eval="True"/>
```

---

## Task 5: Fix .env.demo.example and commit

The `start_demo.sh` and `harden_demo.sh` scripts read `DEMO_ADMIN_PASSWORD` from `.env.demo`, but this variable is missing from the example template.

**Files:**
- Modify: `.env.demo.example`

- [ ] **Step 1: Add the missing variable to `.env.demo.example`**

Open `.env.demo.example` and add at the end:

```bash
# Odoo admin user password (applied by start_demo.sh on each startup)
DEMO_ADMIN_PASSWORD=CHANGE_ME
```

- [ ] **Step 2: Commit all changes so far**

```bash
git add rubicon_addons/rubicon_demo/data/rubicon_demo_data.xml .env.demo.example
git commit -m "feat(demo): enrich demo data and fix env template"
```

- [ ] **Step 3: Push to remote**

```bash
git push
```

---

## Task 6: Pull latest code on the VPS

SSH into the server and pull the changes. All commands below run on the VPS.

- [ ] **Step 1: SSH to the server**

```bash
ssh user@89.168.58.215
```

Replace `user` with your actual SSH username.

- [ ] **Step 2: Go to the project directory and pull**

```bash
cd /path/to/rubicon-demo   # adjust to your actual directory
git pull
```

Verify the new commit appears:
```bash
git log --oneline -3
```
Expected: the `feat(demo): enrich demo data` commit is at the top.

---

## Task 7: Reset and reinitialize the demo database

- [ ] **Step 1: Stop the stack and wipe all volumes**

```bash
docker compose -f docker-compose.demo.yml down -v
```

Expected output: containers stopped, volumes removed.

- [ ] **Step 2: Start the stack**

```bash
docker compose -f docker-compose.demo.yml up -d
```

- [ ] **Step 3: Fix filestore permissions (required after volume recreation)**

```bash
sleep 8
docker compose -f docker-compose.demo.yml exec --user root odoo_demo \
  chown -R odoo:odoo /var/lib/odoo
```

- [ ] **Step 4: Initialize the database (takes 3–5 minutes)**

```bash
docker compose -f docker-compose.demo.yml exec odoo_demo odoo \
  -d rubicondemo \
  -i rubicon_demo,pdp_frontend,sis_frontend,rubicon_uom \
  --stop-after-init
```

Expected: long output ending with `odoo.modules.loading: Modules loaded.` and no `ERROR` lines. If you see errors, check the module name spelling — no spaces between comma-separated names.

- [ ] **Step 5: Restart Odoo in normal mode**

```bash
docker compose -f docker-compose.demo.yml up -d
```

- [ ] **Step 6: Verify Odoo is up**

```bash
curl -s http://localhost:8070/web/health
```

Expected: `{"status": "pass"}` or similar JSON response.

---

## Task 8: Configure .env.demo on the server and harden

- [ ] **Step 1: Set a strong admin password in .env.demo**

```bash
nano .env.demo
```

Add or update:
```bash
DEMO_ADMIN_PASSWORD=<strong-password-here>
```

Generate a strong password with:
```bash
python3 -c "import secrets, string; print(''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(24)))"
```

Save the password somewhere secure (e.g. your password manager).

- [ ] **Step 2: Run harden_demo.sh**

```bash
./ops/harden_demo.sh --restart
```

Expected output ends with:
```
=== Hardening complete ===
```

This sets `list_db=False`, `proxy_mode=True`, generates a strong `admin_passwd`, and restarts Odoo.

- [ ] **Step 3: Apply the admin password via start_demo.sh**

```bash
./ops/start_demo.sh
```

Expected: "Admin password updated." and "Demo server ready."

---

## Task 9: Set up Cloudflare Tunnel

- [ ] **Step 1: Run the tunnel installer as a persistent service**

```bash
./ops/setup_cloudflare_tunnel.sh --service
```

Expected: installs `cloudflared`, creates a systemd service, starts the tunnel.

- [ ] **Step 2: Get the HTTPS URL**

```bash
sudo journalctl -u cloudflared-tunnel -n 50 --no-pager | grep -i trycloudflare
```

Expected: a line containing `https://something.trycloudflare.com`.

Copy this URL — this is what you send to clients.

- [ ] **Step 3: Test the HTTPS URL**

From your local machine (not the server):
```bash
curl -s https://something.trycloudflare.com/web/health
```

Expected: `{"status": "pass"}` — confirms the tunnel is working.

---

## Task 10: Close port 8070 with the firewall

- [ ] **Step 1: Run the firewall script in demo mode**

```bash
./ops/setup_firewall.sh demo
```

Type `y` when prompted. Expected output confirms:
```
✓ 22/tcp   — SSH
✓ 80/tcp   — HTTP
✓ 443/tcp  — HTTPS
✗ 8070     — CLOSED
```

- [ ] **Step 2: If on Oracle Cloud — close port 8070 in the cloud console**

UFW alone is not enough on Oracle Cloud — the cloud security list also needs updating:

1. Go to Oracle Cloud Console → Networking → Virtual Cloud Networks → your VCN → Security Lists
2. In **Ingress Rules**: remove or restrict any rule that allows TCP port 8070 from `0.0.0.0/0`
3. Keep ports 22, 80, 443 open

If you're not on Oracle Cloud, skip this step.

- [ ] **Step 3: Verify port 8070 is no longer reachable from outside**

From your local machine:
```bash
curl --max-time 5 http://89.168.58.215:8070/web/health
```

Expected: connection refused or timeout (not a JSON response).

- [ ] **Step 4: Final smoke test via HTTPS**

Open `https://something.trycloudflare.com` in your browser. You should see the Odoo login page. Log in with `admin` / your `DEMO_ADMIN_PASSWORD`. Check:
- PDP workspace loads and shows demo models
- SIS workspace loads and shows clients + documents with autonumber names (e.g. `SQ-SJC-26001`)
- A document has footnotes visible
- Currency tab in PDP shows USD, EUR, HKD
