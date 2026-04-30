# SIS Document Auto-Numbering Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Automatically generate document names in the format `SO-EMA-25003` when creating a new SIS document — doc-type prefix + client `sis_code` + 2-digit year + 3-digit per-triplet sequence.

**Architecture:** Backend `create()` override on `sis.document` detects partial names (e.g. `SO-EMA-`) and computes the next sequence number atomically via SQL MAX in the same transaction. Frontend updates the name preview to `SO-EMA-` as soon as the customer is selected on an unsaved document.

**Tech Stack:** Odoo 18 Python (TransactionCase tests), OWL 2 JS

---

## File Map

| File | Action | Responsibility |
|---|---|---|
| `rubicon_addons/sis_document/tests/__init__.py` | Create | Test package init |
| `rubicon_addons/sis_document/tests/test_autonumber.py` | Create | Odoo unit tests for auto-numbering |
| `rubicon_addons/sis_document/models/document.py` | Modify | `create()` override — auto-number logic |
| `rubicon_addons/sis_frontend/static/src/js/sis_workspace.js` | Modify | Client-prefix preview + send `doc_type_code` on save |

---

## Task 1: Backend auto-numbering with tests

**Files:**
- Create: `rubicon_addons/sis_document/tests/__init__.py`
- Create: `rubicon_addons/sis_document/tests/test_autonumber.py`
- Modify: `rubicon_addons/sis_document/models/document.py`

- [ ] **Step 1: Create the test package init**

Create `rubicon_addons/sis_document/tests/__init__.py` with:

```python
from . import test_autonumber
```

- [ ] **Step 2: Write the failing tests**

Create `rubicon_addons/sis_document/tests/test_autonumber.py`:

```python
from odoo.tests import common, tagged
from odoo import fields as odoo_fields


@tagged('post_install', '-at_install')
class TestSisDocumentAutoNumber(common.TransactionCase):

    def setUp(self):
        super().setUp()
        self.Doc = self.env['sis.document']
        self.yy = str(odoo_fields.Date.today().year)[2:]
        self.today = odoo_fields.Date.today()

        self.partner_ema = self.env['res.partner'].create({
            'name': 'EMA Test',
            'is_company': True,
            'sis_code': 'EMA',
        })
        self.partner_abc = self.env['res.partner'].create({
            'name': 'ABC Test',
            'is_company': True,
            'sis_code': 'ABC',
        })

    def _make_doc(self, name_prefix):
        return self.Doc.create({
            'name': name_prefix,
            'date_created': self.today,
        })

    def test_first_document_gets_001(self):
        doc = self._make_doc('SO-EMA-')
        self.assertEqual(doc.name, f'SO-EMA-{self.yy}001')

    def test_second_document_increments(self):
        self._make_doc('SO-EMA-')
        doc2 = self._make_doc('SO-EMA-')
        self.assertEqual(doc2.name, f'SO-EMA-{self.yy}002')

    def test_different_doc_type_independent_counter(self):
        self._make_doc('SO-EMA-')
        sq = self._make_doc('SQ-EMA-')
        self.assertEqual(sq.name, f'SQ-EMA-{self.yy}001')

    def test_different_client_independent_counter(self):
        self._make_doc('SO-EMA-')
        doc = self._make_doc('SO-ABC-')
        self.assertEqual(doc.name, f'SO-ABC-{self.yy}001')

    def test_complete_name_not_overwritten(self):
        doc = self.Doc.create({
            'name': 'SO-EMA-25099',
            'date_created': self.today,
        })
        self.assertEqual(doc.name, 'SO-EMA-25099')

    def test_doc_type_code_set_automatically(self):
        doc = self._make_doc('SO-EMA-')
        self.assertEqual(doc.doc_type_code, 'SO')
```

- [ ] **Step 3: Run tests to verify they fail**

```bash
docker compose exec odoo odoo -d rubicon --test-enable -u sis_document --stop-after-init 2>&1 | grep -E "FAIL|ERROR|test_"
```

Expected: all 6 tests FAIL (method `create` not yet overridden).

- [ ] **Step 4: Implement the `create()` override**

Open `rubicon_addons/sis_document/models/document.py`. Add `api` to the import and add the `create()` method at the end of the class, before the closing line:

```python
from odoo import models, fields, api   # replace existing import line


class SisDocument(models.Model):
    # ... (all existing fields unchanged) ...

    def get_ornament_quantities(self):
        # ... unchanged ...

    def action_print_pdf(self):
        # ... unchanged ...

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            name = vals.get('name', '')
            parts = name.split('-')
            # Partial prefix detected: "SO-EMA-" → ['SO', 'EMA', '']
            if len(parts) == 3 and parts[2] == '':
                doc_type, client_code = parts[0], parts[1]
                date = vals.get('date_created') or fields.Date.today()
                # date arrives as string "2025-01-15" via JSON-RPC
                if isinstance(date, str):
                    yy = date[2:4]
                else:
                    yy = str(date.year)[2:]
                prefix = f'{doc_type}-{client_code}-{yy}'
                self.env.cr.execute(
                    "SELECT MAX(name) FROM sis_document WHERE name LIKE %s",
                    [prefix + '%']
                )
                row = self.env.cr.fetchone()
                last = row[0] if row and row[0] else None
                seq = (int(last[-3:]) + 1) if last else 1
                vals['name'] = f'{prefix}{seq:03d}'
                vals['doc_type_code'] = doc_type
        return super().create(vals_list)
```

The full updated file (complete replacement of the class, preserving all existing content):

```python
from odoo import models, fields, api


class SisDocument(models.Model):
    _name = 'sis.document'
    _description = 'SIS Sales Document'
    _rec_name = 'name'
    _order = 'date_created desc, id desc'

    # Header
    name = fields.Char(string='Doc Name', required=True, index=True)
    doc_type_id = fields.Many2one('sis.doc.type', string='Document Type')
    doc_type_code = fields.Char(string='Doc Type Code', index=True)
    legacy_id = fields.Integer(string='Legacy ID', index=True)

    # Status
    closed = fields.Boolean(default=False)
    canceled = fields.Boolean(default=False)

    # Dates
    date_created = fields.Date(string='Created')
    date_due = fields.Date(string='Due Date')

    # Party
    party_id = fields.Many2one('res.partner', string='Customer')
    party_code = fields.Char(string='Customer Code')

    # General
    margin_id = fields.Many2one('pdp.margin', string='Margin')
    margin_name = fields.Char(string='Margin Name')
    currency_id = fields.Many2one('res.currency', string='Currency')
    currency_legacy = fields.Char(string='Currency (legacy)')
    notes = fields.Text()
    footnotes = fields.Text()

    # Payment
    pay_term_id = fields.Many2one('sis.pay.term', string='Payment Term')

    # Order specific
    customer_po = fields.Char(string='Customer P.O. No.')
    rcv_mode_id = fields.Many2one('sis.doc.in.mode', string='Receiving Mode')
    trade_fair_id = fields.Many2one('sis.trade.fair', string='Trade Fair')
    employee = fields.Char()

    # Shipment
    ship_address = fields.Text(string='Ship To Address')
    ship_method_id = fields.Many2one('sis.shipper', string='Ship Method')
    ship_consignee_bank = fields.Boolean(string='Consignee Bank')
    ship_for_acc_of = fields.Char(string='For Account Of')
    ship_book = fields.Char(string='Book')
    ship_page = fields.Char(string='Page')

    # Financials (computed in legacy, stored here for import)
    total_fob = fields.Float(string='Total F.O.B', digits=(12, 2))
    freight_insurance = fields.Float(string='Freight & Insurance', digits=(12, 2))
    total_cif = fields.Float(string='Total C.I.F', digits=(12, 2))
    deposit = fields.Float(string='Less Deposit', digits=(12, 2))
    total_amount = fields.Float(string='Total Amount', digits=(12, 2))
    total_qty = fields.Integer(string='Total Qty')
    total_cost = fields.Float(string='Total Cost', digits=(12, 2))
    total_profit = fields.Float(string='Total Profit', digits=(12, 2))
    profit_pct = fields.Float(string='Profit %', digits=(6, 2))

    # Company info stamp
    stamp = fields.Text(string='Stamp')

    # Items
    item_ids = fields.One2many('sis.document.item', 'document_id', string='Items')

    # Child documents
    child_doc_ids = fields.Many2many(
        'sis.document', 'sis_doc_parent_child_rel',
        'parent_id', 'child_id', string='Child Documents')

    def get_ornament_quantities(self):
        """Return {category_name: total_qty} grouped by product category."""
        counts = {}
        for item in self.item_ids:
            cat_name = item.get_category_name() or 'Other'
            counts[cat_name] = counts.get(cat_name, 0) + int(item.qty)
        return counts

    def action_print_pdf(self):
        return self.env.ref('sis_document.action_report_sis_document').report_action(self)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            name = vals.get('name', '')
            parts = name.split('-')
            # Partial prefix: "SO-EMA-" → ['SO', 'EMA', '']
            if len(parts) == 3 and parts[2] == '':
                doc_type, client_code = parts[0], parts[1]
                date = vals.get('date_created') or fields.Date.today()
                # date arrives as string "2025-01-15" via JSON-RPC
                if isinstance(date, str):
                    yy = date[2:4]
                else:
                    yy = str(date.year)[2:]
                prefix = f'{doc_type}-{client_code}-{yy}'
                self.env.cr.execute(
                    "SELECT MAX(name) FROM sis_document WHERE name LIKE %s",
                    [prefix + '%']
                )
                row = self.env.cr.fetchone()
                last = row[0] if row and row[0] else None
                seq = (int(last[-3:]) + 1) if last else 1
                vals['name'] = f'{prefix}{seq:03d}'
                vals['doc_type_code'] = doc_type
        return super().create(vals_list)
```

- [ ] **Step 5: Run tests to verify they pass**

```bash
docker compose exec odoo odoo -d rubicon --test-enable -u sis_document --stop-after-init 2>&1 | grep -E "FAIL|ERROR|OK|test_"
```

Expected: all 6 tests PASS, no FAIL or ERROR.

- [ ] **Step 6: Commit**

```bash
git add rubicon_addons/sis_document/tests/__init__.py \
        rubicon_addons/sis_document/tests/test_autonumber.py \
        rubicon_addons/sis_document/models/document.py
git commit -m "feat(sis): auto-number documents on create (SO-EMA-25001 format)"
```

---

## Task 2: Frontend client-prefix preview

**Files:**
- Modify: `rubicon_addons/sis_frontend/static/src/js/sis_workspace.js`

- [ ] **Step 1: Update `onCustomerChange()` to set partial prefix**

In `sis_workspace.js`, find the `onCustomerChange` method (around line 551). After the existing block that reads the partner's `sis_pay_term_id`, add the name-preview logic. The full updated method:

```js
async onCustomerChange(ev) {
    const id = parseInt(ev.target.value) || false;
    this.state.doc.party_id = id;
    this.state.docDirty = true;
    if (id) {
        const [p] = await this.orm.read("res.partner", [id],
            ["sis_pay_term_id"]);
        if (p) {
            if (!this._m2oId(this.state.doc.pay_term_id) && p.sis_pay_term_id)
                this.state.doc.pay_term_id = p.sis_pay_term_id;
        }
        // Set partial name preview for unsaved documents
        if (!this.state.doc.id) {
            const partner = this.sisPartners.find(pt => pt.id === id);
            if (partner?.sis_code) {
                this.state.doc.name = `${this.state.docType}-${partner.sis_code}-`;
            }
        }
    }
    await this._fetchPartyAddress(id);
}
```

- [ ] **Step 2: Send `doc_type_code` in `saveDocument()`**

In the same file, find `saveDocument()` (around line 654). Add `doc_type_code` to the `vals` object so newly created documents have it stored correctly. Find this block:

```js
        const vals = {
            name: d.name,
            closed: d.closed || false,
```

Replace with:

```js
        const vals = {
            name: d.name,
            doc_type_code: d.doc_type_code || this.state.docType || "",
            closed: d.closed || false,
```

- [ ] **Step 3: Manual test**

Restart the Odoo server and navigate to a document section (SO, SQ, or SI):

```bash
docker compose restart odoo
```

1. Click **New Document**
2. Verify the name field shows `SO-` (or `SQ-`, `SI-` depending on section)
3. Select a customer with a `sis_code` (e.g. EMA)
4. Verify the name field updates to `SO-EMA-`
5. Fill in other fields and click **Save**
6. Verify the document name becomes `SO-EMA-{yy}XXX` where `yy` is current year and `XXX` is the next sequence number for that triplet

- [ ] **Step 4: Commit**

```bash
git add rubicon_addons/sis_frontend/static/src/js/sis_workspace.js
git commit -m "feat(sis_frontend): show client-prefix preview on new document"
```
