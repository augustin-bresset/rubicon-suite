# Odoo Partner Alignment Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace all SIS-custom ship/contact fields on `res.partner` with standard Odoo structures (`type='delivery'` child partner, `type='contact'` child partner, `state_id` M2O).

**Architecture:** The BCP import pipeline (raw_to_data_sis.py → sis.party.csv → sync_parties.py → Odoo) gains two new derived child `res.partner` records per company. The model sheds five custom fields. The frontend reads children via `orm.search_read` filtered by `type`. No new Odoo modules required.

**Tech Stack:** Python 3, Odoo 18 ORM (`res.partner`), XML-RPC (`xmlrpc.client`), OWL 2 (frontend), pytest (converter tests).

---

## File Map

| File | Action | Responsibility |
|---|---|---|
| `rubicon_addons/sis_party/models/partner.py` | Modify | Remove 6 obsolete custom fields |
| `rubicon_addons/rubicon_import/raw_to_data/raw_to_data_sis.py` | Modify | Emit `state_code` + `sis_ship_state_code` in CSV row |
| `rubicon_addons/rubicon_import/raw_to_data/test_sis_converter.py` | Modify | Tests for new fields, assert removed fields absent |
| `ops/setup/sync_parties.py` | Modify | Create/update `type='delivery'` and `type='contact'` children; resolve `state_id` |
| `rubicon_addons/sis_frontend/static/src/js/sis_workspace.js` | Modify | Load children by type; save to child partners |
| `rubicon_addons/sis_frontend/static/src/xml/sis_workspace.xml` | Modify | Bind General/Shipment tabs to child partner state |

---

## Task 1 — Remove obsolete custom fields from the model

**Files:**
- Modify: `rubicon_addons/sis_party/models/partner.py`

The six fields being removed all have a proper Odoo equivalent that will be carried by child `res.partner` records:

| Removed field | Odoo replacement |
|---|---|
| `sis_contact` (Char) | `res.partner(type='contact').name` |
| `sis_ship_address` (Text) | `res.partner(type='delivery').street/street2` |
| `sis_ship_city` (Char) | `res.partner(type='delivery').city` |
| `sis_ship_state` (Char) | `res.partner(type='delivery').state_id` |
| `sis_ship_zip` (Char) | `res.partner(type='delivery').zip` |
| `sis_ship_country_id` (M2O res.country) | `res.partner(type='delivery').country_id` |

Keep: `sis_ship_fedex_acc`, `sis_ship_stamp`, `sis_ship_method_id` — these have no Odoo equivalent.

- [ ] **Step 1: Edit `partner.py`**

Replace the current file content with:

```python
from odoo import models, fields


class ResPartnerPhone(models.Model):
    _name = 'res.partner.phone'
    _description = 'Additional Phone Numbers'

    partner_id = fields.Many2one('res.partner', required=True, ondelete='cascade')
    name = fields.Char('Label')
    phone = fields.Char('Phone Number', required=True)


class ResPartnerBank(models.Model):
    _inherit = 'res.partner.bank'

    sis_bank_name    = fields.Char('Bank Name')
    sis_bank_address = fields.Text('Bank Address')


class ResPartner(models.Model):
    _inherit = 'res.partner'

    sis_code    = fields.Char('SIS Code', index=True)
    sis_group   = fields.Char('SIS Group')

    sis_is_customer = fields.Boolean('Is a Customer', default=False)
    sis_is_vendor   = fields.Boolean('Is a Vendor',   default=False)

    sis_phone_ids = fields.One2many('res.partner.phone', 'partner_id', string='Additional Phones')

    margin_id        = fields.Many2one('pdp.margin',  string='Margin')
    sis_pay_term_id  = fields.Many2one('sis.pay.term', string='SIS Payment Term')
    sis_account      = fields.Char('SIS Account')

    sis_vendor_account      = fields.Char('Vendor Account')
    sis_vendor_pay_term_id  = fields.Many2one('sis.pay.term', string='Vendor Payment Term')

    # Shipment — only SIS-specific fields without an Odoo equivalent
    sis_ship_method_id  = fields.Many2one('sis.shipper', string='Default Shipping Method')
    sis_ship_fedex_acc  = fields.Char('FedEx Account')
    sis_ship_stamp      = fields.Text('Stamp')
```

- [ ] **Step 2: Upgrade the module to apply the model change**

```bash
docker compose exec odoo odoo -d rubicon -u sis_party --stop-after-init
```

Expected: no errors. The six columns are dropped from `res_partner` (Odoo handles `DROP COLUMN` automatically on upgrade).

- [ ] **Step 3: Commit**

```bash
git add rubicon_addons/sis_party/models/partner.py
git commit -m "refactor(sis_party): replace custom ship/contact fields with standard Odoo child partners"
```

---

## Task 2 — Add `state_code` and `sis_ship_state_code` to the converter

**Files:**
- Modify: `rubicon_addons/rubicon_import/raw_to_data/raw_to_data_sis.py`

The BCP data contains state abbreviations at fixed offsets relative to `cc_col`:
- Main address state: `cc_col - 2` (e.g. "FL        " for A&J)
- Ship address state: `scc - 2` where `scc` is the ship country-code column found by the heuristic

These are added to the CSV row as plain string columns (`state_code`, `sis_ship_state_code`).  
`sync_parties.py` will resolve them to `state_id` via Odoo XML-RPC.

- [ ] **Step 1: Write the failing test first**

In `test_sis_converter.py`, add inside `TestParty7AJ`:

```python
def test_state_code_exported(self):
    assert 'state_code' in self.company
    assert self.company['state_code'] == 'FL'

def test_ship_state_code_exported(self):
    assert 'sis_ship_state_code' in self.company
    assert self.company['sis_ship_state_code'] == 'FL'
```

Run: `python3 -m pytest rubicon_addons/rubicon_import/raw_to_data/test_sis_converter.py::TestParty7AJ::test_state_code_exported -v`
Expected: **FAIL** — `KeyError` or assertion error.

- [ ] **Step 2: Add `state_code` to the company yield in `raw_to_data_sis.py`**

Inside `make_row_to_party`, in the main `yield {...}` block, add:

```python
'state_code': _get(row, cc_col - 2).strip() if cc_col is not None else '',
```

- [ ] **Step 3: Add `sis_ship_state_code` — extend the ship heuristic**

Replace the current ship-address heuristic block:

```python
ship_city = ship_zip = ship_cc = ''
if cc_col is not None:
    search_from = (contact_name_col if contact_name_col is not None else cc_col + 14) + 3
    for i in range(search_from, min(len(row), 70)):
        if row[i].strip().upper() in country_names:
            scc = i + 4
            if scc < len(row) and row[scc].strip() in country_codes:
                ship_city = _get(row, scc - 3)
                ship_zip  = _get(row, scc - 1)
                ship_cc   = _get(row, scc)
                break
fedex_acc = s(row[-2]) if len(row) >= 2 else ''
```

With:

```python
ship_city = ship_zip = ship_cc = ship_state = ''
if cc_col is not None:
    search_from = (contact_name_col if contact_name_col is not None else cc_col + 14) + 3
    for i in range(search_from, min(len(row), 70)):
        if row[i].strip().upper() in country_names:
            scc = i + 4
            if scc < len(row) and row[scc].strip() in country_codes:
                ship_city  = _get(row, scc - 3)
                ship_state = _get(row, scc - 2).strip()
                ship_zip   = _get(row, scc - 1)
                ship_cc    = _get(row, scc)
                break
fedex_acc = s(row[-2]) if len(row) >= 2 else ''
```

Add `'sis_ship_state_code': ship_state,` to the yield dict.

- [ ] **Step 4: Add both columns to the `__main__` fieldnames list**

```python
fieldnames=['id', 'sis_code', 'name', 'active', 'customer_rank', 'supplier_rank',
            'is_company', 'street', 'street2',
            'city', 'state_code', 'zip', 'country_id',
            'phone', 'mobile', 'email', 'website', 'notes',
            'sis_is_customer', 'sis_is_vendor', 'sis_contact',
            'margin_id', 'sis_pay_term_id', 'sis_ship_method_id',
            'sis_ship_fedex_acc',
            'sis_ship_city', 'sis_ship_state_code', 'sis_ship_zip', 'sis_ship_country_id',
            'sis_ship_stamp'],
```

- [ ] **Step 5: Run tests**

```bash
python3 -m pytest rubicon_addons/rubicon_import/raw_to_data/test_sis_converter.py -v
```

Expected: all 39 tests pass.

- [ ] **Step 6: Regenerate the CSV**

```bash
PYTHONPATH=rubicon_addons python3 rubicon_addons/rubicon_import/raw_to_data/raw_to_data_sis.py
```

- [ ] **Step 7: Commit**

```bash
git add rubicon_addons/rubicon_import/raw_to_data/raw_to_data_sis.py \
        rubicon_addons/rubicon_import/raw_to_data/test_sis_converter.py \
        rubicon_addons/sis_party/data/sis.party.csv
git commit -m "feat(converter): add state_code and sis_ship_state_code columns to sis.party.csv"
```

---

## Task 3 — Update tests: assert removed fields are gone

**Files:**
- Modify: `rubicon_addons/rubicon_import/raw_to_data/test_sis_converter.py`

The model no longer has `sis_contact`, `sis_ship_address`, `sis_ship_city`, `sis_ship_state`, `sis_ship_zip`, `sis_ship_country_id`. Columns with these names still exist in the CSV (used by `sync_parties.py`) but the column names no longer match model fields.

- [ ] **Step 1: Replace the old ship/contact assertions**

Remove the tests:
- `test_sis_contact_name` (field removed from model — now a child partner)
- `test_ship_city` (replaced by `test_state_code_exported` added in Task 2)
- `test_ship_zip`
- `test_ship_country_odoo_name`

Add in their place:

```python
# ── ship data still present in CSV row (used by sync_parties) ─────────────

def test_ship_city_in_csv(self):
    # Not a model field anymore; lives in the child delivery partner
    # but must still be in the CSV dict for sync_parties.py to use
    assert self.company['sis_ship_city'] == 'MIAMI'

def test_ship_zip_in_csv(self):
    assert self.company['sis_ship_zip'] == '33143'

def test_ship_country_in_csv(self):
    assert self.company['sis_ship_country_id'] == 'United States'

def test_ship_state_code_in_csv(self):
    assert self.company['sis_ship_state_code'] == 'FL'

# ── contact name still in CSV (used by sync_parties) ─────────────────────

def test_contact_name_in_csv(self):
    assert self.company['sis_contact'] == 'Mr. Jose V. ROSAS'
```

- [ ] **Step 2: Run all tests**

```bash
python3 -m pytest rubicon_addons/rubicon_import/raw_to_data/test_sis_converter.py -v
```

Expected: 39 tests pass.

- [ ] **Step 3: Commit**

```bash
git add rubicon_addons/rubicon_import/raw_to_data/test_sis_converter.py
git commit -m "test(converter): update assertions for Odoo-aligned partner structure"
```

---

## Task 4 — Update `sync_parties.py`: create child delivery and contact partners

**Files:**
- Modify: `ops/setup/sync_parties.py`

For each company row:
1. Update the main `res.partner` (company) as before — `state_id` resolved from `state_code`
2. Find or create a `type='delivery'` child with the ship address data
3. Find or create a `type='contact'` child with the contact person name

State resolution: load all `res.country.state` records, index by `(country_id, code.upper())`.

- [ ] **Step 1: Add state lookup at the top of the script (after country lookup)**

```python
print("Loading res.country.state...")
states = sr('res.country.state', [], ['id', 'code', 'country_id'])
# key: (country_odoo_id, 'FL')  →  state_id
state_by_country_code = {
    (s['country_id'][0], s['code'].upper()): s['id']
    for s in states
}
print(f"  {len(states)} states loaded")

def resolve_state(state_code, country_odoo_id):
    if not state_code or not country_odoo_id:
        return None
    return state_by_country_code.get((country_odoo_id, state_code.strip().upper()))
```

- [ ] **Step 2: Load existing delivery and contact children (index by parent sis_code)**

After loading `partner_by_code`:

```python
print("Loading existing child partners (delivery + contact)...")
children = sr('res.partner',
              [('type', 'in', ['delivery', 'contact']),
               ('parent_id', 'in', list(partner_by_code.values()))],
              ['id', 'type', 'parent_id'])

delivery_by_parent = {}
contact_by_parent  = {}
for c in children:
    pid = c['parent_id'][0]
    if c['type'] == 'delivery':
        delivery_by_parent[pid] = c['id']
    elif c['type'] == 'contact':
        contact_by_parent[pid] = c['id']
print(f"  {len(delivery_by_parent)} delivery addresses, {len(contact_by_parent)} contacts found")
```

- [ ] **Step 3: Inside the main loop — resolve `state_id` for the company record**

In the `vals` build section (after resolving `country_id`), add:

```python
state_code = row.get('state_code', '').strip()
cid_for_state = vals.get('country_id') or (resolve_country(row.get('country_id', '')))
sid = resolve_state(state_code, cid_for_state)
if sid:
    vals['state_id'] = sid
```

- [ ] **Step 4: After writing the company record — upsert delivery child**

Add after `do_write('res.partner', [partner_id], vals)`:

```python
# ── Delivery child ────────────────────────────────────────────────────────
ship_country_name = row.get('sis_ship_country_id', '').strip()
ship_country_id   = resolve_country(ship_country_name)
ship_city         = row.get('sis_ship_city', '').strip()
ship_zip          = row.get('sis_ship_zip', '').strip()
ship_state_code   = row.get('sis_ship_state_code', '').strip()
ship_state_id     = resolve_state(ship_state_code, ship_country_id)

delivery_vals = {'type': 'delivery', 'parent_id': partner_id,
                 'name': company_name}
if ship_city:
    delivery_vals['city'] = ship_city
if ship_zip:
    delivery_vals['zip'] = ship_zip
if ship_country_id:
    delivery_vals['country_id'] = ship_country_id
if ship_state_id:
    delivery_vals['state_id'] = ship_state_id

if delivery_vals.get('city') or delivery_vals.get('country_id'):
    existing_delivery = delivery_by_parent.get(partner_id)
    if existing_delivery:
        do_write('res.partner', [existing_delivery], delivery_vals)
    else:
        if not DRY_RUN:
            new_id = models.execute_kw(DB, uid, PASS, 'res.partner', 'create', [delivery_vals])
            delivery_by_parent[partner_id] = new_id

# ── Contact child ─────────────────────────────────────────────────────────
contact_name = row.get('sis_contact', '').strip()
if contact_name:
    contact_vals = {'type': 'contact', 'parent_id': partner_id,
                    'name': contact_name, 'is_company': False}
    existing_contact = contact_by_parent.get(partner_id)
    if existing_contact:
        do_write('res.partner', [existing_contact], contact_vals)
    else:
        if not DRY_RUN:
            new_id = models.execute_kw(DB, uid, PASS, 'res.partner', 'create', [contact_vals])
            contact_by_parent[partner_id] = new_id
```

- [ ] **Step 5: Run dry-run and verify A&J output**

```bash
python3 ops/setup/sync_parties.py --dry-run 2>&1 | grep -A3 "DRY.*A&J\|EMA"
```

Expected: shows city, state, delivery and contact creation for A&J.

- [ ] **Step 6: Run for real**

```bash
python3 ops/setup/sync_parties.py
```

- [ ] **Step 7: Verify in DB**

```bash
docker compose exec db psql -U rubicondev -d rubicon -c "
SELECT p.sis_code, p.city, p.state_id, c.type, c.name, c.city
FROM res_partner p
LEFT JOIN res_partner c ON c.parent_id = p.id AND c.type IN ('delivery','contact')
WHERE p.sis_code = 'A\&J'
ORDER BY c.type;"
```

Expected:
```
 sis_code | city  | state_id | type     |       name        |  city
----------+-------+----------+----------+-------------------+-------
 A&J      | MIAMI |    <id>  | contact  | Mr. Jose V. ROSAS |
 A&J      | MIAMI |    <id>  | delivery | A&J INTERNATIONAL | MIAMI
```

- [ ] **Step 8: Commit**

```bash
git add ops/setup/sync_parties.py
git commit -m "feat(sync): create delivery/contact child partners and resolve state_id"
```

---

## Task 5 — Update the frontend JS

**Files:**
- Modify: `rubicon_addons/sis_frontend/static/src/js/sis_workspace.js`

**Current state:** `_loadParty` reads `sis_contact`, `sis_ship_address`, `sis_ship_city`, `sis_ship_zip`, `sis_ship_country_id` directly from the company partner.

**New state:**
- `state.deliveryPartner` — the `type='delivery'` child, or a blank object
- `state.contactPartner`  — the `type='contact'` child, or a blank object
- General tab binds to `state.contactPartner.name`
- Shipment tab binds to `state.deliveryPartner.{street, city, state_id, zip, country_id}`

- [ ] **Step 1: Add `deliveryPartner` and `contactPartner` to `state` initialisation**

Find the `useState` initialisation block (search for `partyTab`) and add:

```javascript
deliveryPartner: null,
contactPartner:  null,
```

- [ ] **Step 2: Replace `_loadParty` to remove old fields and load children**

Find `_loadParty(partyId)`. Replace the field list and add child loading:

```javascript
async _loadParty(partyId) {
    const records = await this.orm.read("res.partner", [partyId], [
        "id", "name", "category_id", "active",
        "title", "street", "street2", "city", "state_id", "zip", "country_id",
        "phone", "mobile", "email", "website", "comment",
        "margin_id", "sis_pay_term_id",
        "sis_is_customer", "sis_is_vendor",
        "sis_account", "sis_vendor_account", "sis_vendor_pay_term_id",
        "sis_ship_method_id", "sis_ship_fedex_acc", "sis_ship_stamp",
        "bank_ids", "sis_phone_ids", "sis_code"
    ]);
    this.state.party = records[0] ? { ...records[0] } : null;
    this.state.partyDirty = false;

    // Load delivery address child
    const deliveryList = await this.orm.searchRead("res.partner",
        [["parent_id", "=", partyId], ["type", "=", "delivery"]],
        ["id", "name", "street", "street2", "city", "state_id", "zip", "country_id"],
        { limit: 1 }
    );
    this.state.deliveryPartner = deliveryList.length
        ? { ...deliveryList[0] }
        : { id: null, name: "", street: "", street2: "", city: "",
            state_id: false, zip: "", country_id: false };

    // Load contact child
    const contactList = await this.orm.searchRead("res.partner",
        [["parent_id", "=", partyId], ["type", "=", "contact"], ["is_company", "=", false]],
        ["id", "name", "function"],
        { limit: 1 }
    );
    this.state.contactPartner = contactList.length
        ? { ...contactList[0] }
        : { id: null, name: "", function: "" };

    // Bank / phones (unchanged)
    if (this.state.party?.bank_ids?.length) {
        this.state.partyBanks = await this.orm.read("res.partner.bank",
            this.state.party.bank_ids, ["bank_id", "acc_holder_name", "acc_number"]);
    } else {
        this.state.partyBanks = [];
    }
    if (this.state.party?.sis_phone_ids?.length) {
        this.state.partyPhones = await this.orm.read("res.partner.phone",
            this.state.party.sis_phone_ids, ["name", "phone"]);
    } else {
        this.state.partyPhones = [];
    }

    const idx = this.state.parties.findIndex(p => p.id === partyId);
    if (idx >= 0) this.state.partyIndex = idx;
},
```

- [ ] **Step 3: Add `setDeliveryField` and `setContactField` helper methods**

After `setPartyField`:

```javascript
setDeliveryField(field, value) {
    this.state.deliveryPartner[field] = value;
    this.state.partyDirty = true;
},

setContactField(field, value) {
    this.state.contactPartner[field] = value;
    this.state.partyDirty = true;
},
```

- [ ] **Step 4: Update `saveParty` to persist delivery and contact children**

Find the `saveParty` (or equivalent save method). After writing the main partner, add:

```javascript
// Save delivery child
const dp = this.state.deliveryPartner;
const deliveryVals = {
    type: "delivery", parent_id: savedId,
    name: this.state.party.name,
    street: dp.street || "", street2: dp.street2 || "",
    city: dp.city || "", zip: dp.zip || "",
    state_id: this._m2oId(dp.state_id) || false,
    country_id: this._m2oId(dp.country_id) || false,
};
if (dp.id) {
    await this.orm.write("res.partner", [dp.id], deliveryVals);
} else if (dp.city || dp.country_id) {
    const [newId] = await this.orm.create("res.partner", [deliveryVals]);
    this.state.deliveryPartner.id = newId;
}

// Save contact child
const cp = this.state.contactPartner;
if (cp.name) {
    const contactVals = {
        type: "contact", parent_id: savedId,
        name: cp.name, is_company: false,
    };
    if (cp.id) {
        await this.orm.write("res.partner", [cp.id], contactVals);
    } else {
        const [newId] = await this.orm.create("res.partner", [contactVals]);
        this.state.contactPartner.id = newId;
    }
}
```

- [ ] **Step 5: Update `newParty` to initialise `deliveryPartner` and `contactPartner`**

In the `newParty()` method, add after the party object:

```javascript
this.state.deliveryPartner = {
    id: null, name: "", street: "", street2: "",
    city: "", state_id: false, zip: "", country_id: false
};
this.state.contactPartner = { id: null, name: "", function: "" };
```

- [ ] **Step 6: Commit (JS only — template in next task)**

```bash
git add rubicon_addons/sis_frontend/static/src/js/sis_workspace.js
git commit -m "feat(sis_frontend): load delivery/contact child partners for General and Shipment tabs"
```

---

## Task 6 — Update the frontend XML template

**Files:**
- Modify: `rubicon_addons/sis_frontend/static/src/xml/sis_workspace.xml`

- [ ] **Step 1: Update the Contact field in the General tab**

Find the input/field bound to `sis_contact` (search for `sis_contact` in the XML). Replace with:

```xml
<input type="text" class="o_input"
       t-att-value="state.contactPartner.name || ''"
       t-on-input="ev => this.setContactField('name', ev.target.value)"
       placeholder="Contact name"/>
```

- [ ] **Step 2: Update the Shipment tab address fields**

Find the Shipment tab section (search for `sis_ship_address` or `sis_ship_city`). Replace all `sis_ship_*` address bindings with individual standard-field bindings:

```xml
<!-- Street -->
<input type="text" class="o_input"
       t-att-value="state.deliveryPartner.street || ''"
       t-on-input="ev => this.setDeliveryField('street', ev.target.value)"
       placeholder="Street"/>
<!-- City -->
<input type="text" class="o_input"
       t-att-value="state.deliveryPartner.city || ''"
       t-on-input="ev => this.setDeliveryField('city', ev.target.value)"
       placeholder="City"/>
<!-- Zip -->
<input type="text" class="o_input"
       t-att-value="state.deliveryPartner.zip || ''"
       t-on-input="ev => this.setDeliveryField('zip', ev.target.value)"
       placeholder="Zip"/>
<!-- Country (M2O select — reuse the same pattern as party.country_id) -->
<select class="o_input"
        t-on-change="ev => this.setDeliveryField('country_id', parseInt(ev.target.value) || false)">
    <option value="">—</option>
    <t t-foreach="allCountries" t-as="c" t-key="c.id">
        <option t-att-value="c.id"
                t-att-selected="c.id === this._m2oId(state.deliveryPartner.country_id)">
            <t t-esc="c.name"/>
        </option>
    </t>
</select>
```

- [ ] **Step 3: Upgrade and test in browser**

```bash
docker compose exec odoo odoo -d rubicon -u sis_frontend --stop-after-init \
  && docker compose restart odoo
```

Open the SIS frontend, select A&J INTERNATIONAL:
- **General tab → Contact**: shows "Mr. Jose V. ROSAS"
- **Shipment tab → City**: shows "MIAMI"
- **Shipment tab → Country**: shows "United States"

- [ ] **Step 4: Commit**

```bash
git add rubicon_addons/sis_frontend/static/src/xml/sis_workspace.xml
git commit -m "feat(sis_frontend): bind General contact and Shipment address to child partner records"
```

---

## Self-Review

**Spec coverage:**
- ✅ `sis_contact` removed → `type='contact'` child
- ✅ `sis_ship_*` address fields removed → `type='delivery'` child
- ✅ `state_id` M2O resolved via sync script
- ✅ CSV converter adds `state_code` + `sis_ship_state_code`
- ✅ Tests updated (39 total)
- ✅ Frontend reads from children, saves to children

**Known out-of-scope (no Odoo equivalent, kept as custom):**
- `sis_ship_method_id` → `sis.shipper` (no `delivery` module)
- `sis_ship_fedex_acc`, `sis_ship_stamp`
- `sis_pay_term_id` → `sis.pay.term` (no `account` module)
- `margin_id` → `pdp.margin`
- Bank info (`res.partner.bank`) — separate future task

**Placeholder scan:** No TBD, no TODO, no "similar to Task N". All code blocks are complete.

**Type consistency:** `state.deliveryPartner`, `state.contactPartner`, `setDeliveryField`, `setContactField` — used consistently across Tasks 5 and 6.
