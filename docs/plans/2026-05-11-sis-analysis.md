# SIS Analysis Module — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create a new Odoo 18 module `sis_analysis` that exposes `sis.document` data as a native pivot/graph/list analysis view — the Odoo equivalent of the legacy Windows Analysis application.

**Architecture:** New module with no new data model; extends `sis.document` with three stored computed fields (`analysis_year`, `analysis_region_id`, `analysis_country_id`) to enable group-by in views. All UI is pure Odoo XML (pivot, graph, list, search views) with no custom JavaScript.

**Tech Stack:** Odoo 18, Python 3, XML views, `res.country.group` for region mapping, Docker Compose for upgrade/test commands.

---

## File Map

| File | Action | Responsibility |
|---|---|---|
| `rubicon_addons/sis_analysis/__manifest__.py` | Create | Module metadata and data file list |
| `rubicon_addons/sis_analysis/__init__.py` | Create | Package init, imports models |
| `rubicon_addons/sis_analysis/models/__init__.py` | Create | Package init, imports model file |
| `rubicon_addons/sis_analysis/models/sis_document_analysis.py` | Create | Extends `sis.document` with `analysis_year`, `analysis_region_id`, `analysis_country_id` |
| `rubicon_addons/sis_analysis/views/analysis_views.xml` | Create | Pivot, graph, list, search views + window action |
| `rubicon_addons/sis_analysis/views/menus.xml` | Create | Menu entry under "SIS Document" root |
| `rubicon_addons/sis_analysis/tests/__init__.py` | Create | Test package init |
| `rubicon_addons/sis_analysis/tests/test_analysis_fields.py` | Create | Tests for the three computed fields |

---

## Task 1: Module Scaffold

**Files:**
- Create: `rubicon_addons/sis_analysis/__manifest__.py`
- Create: `rubicon_addons/sis_analysis/__init__.py`
- Create: `rubicon_addons/sis_analysis/models/__init__.py`
- Create: `rubicon_addons/sis_analysis/models/sis_document_analysis.py` (stub only)
- Create: `rubicon_addons/sis_analysis/views/analysis_views.xml` (empty placeholder)
- Create: `rubicon_addons/sis_analysis/views/menus.xml` (empty placeholder)
- Create: `rubicon_addons/sis_analysis/tests/__init__.py`

- [ ] **Step 1.1: Create `__manifest__.py`**

```python
{
    'name': 'SIS Analysis',
    'version': '18.0.1.0.0',
    'license': 'LGPL-3',
    'category': 'Sales',
    'summary': 'Sales & Orders pivot analysis',
    'depends': ['base', 'sis_document', 'sis_party'],
    'data': [
        'views/analysis_views.xml',
        'views/menus.xml',
    ],
    'installable': True,
    'application': False,
}
```

- [ ] **Step 1.2: Create `__init__.py`**

```python
from . import models
```

- [ ] **Step 1.3: Create `models/__init__.py`**

```python
from . import sis_document_analysis
```

- [ ] **Step 1.4: Create `models/sis_document_analysis.py` (stub — fields come in Task 3)**

```python
from odoo import models, fields, api


class SisDocumentAnalysis(models.Model):
    _inherit = 'sis.document'
```

- [ ] **Step 1.5: Create `views/analysis_views.xml` (minimal valid XML)**

```xml
<?xml version="1.0" encoding="utf-8"?>
<odoo>
</odoo>
```

- [ ] **Step 1.6: Create `views/menus.xml` (minimal valid XML)**

```xml
<?xml version="1.0" encoding="utf-8"?>
<odoo>
</odoo>
```

- [ ] **Step 1.7: Create `tests/__init__.py`**

```python
from . import test_analysis_fields
```

- [ ] **Step 1.8: Install the module to verify the scaffold is error-free**

```bash
docker compose exec odoo odoo -d rubicon -i sis_analysis --stop-after-init
```

Expected: install completes without Python errors or XML parse failures. No "WARNING" about missing dependencies.

- [ ] **Step 1.9: Commit**

```bash
git add rubicon_addons/sis_analysis/
git commit -m "feat(sis_analysis): scaffold new analysis module"
```

---

## Task 2: Write Failing Tests for Computed Fields

**Files:**
- Create: `rubicon_addons/sis_analysis/tests/test_analysis_fields.py`

- [ ] **Step 2.1: Create `tests/test_analysis_fields.py`**

```python
from odoo.tests import common, tagged
from datetime import date


@tagged('post_install', '-at_install')
class TestSisDocumentAnalysisFields(common.TransactionCase):

    def setUp(self):
        super().setUp()
        self.region = self.env['res.country.group'].create({'name': '_Test Region'})
        self.country = self.env['res.country'].search([('code', '=', 'FR')], limit=1)
        self.country.country_group_ids = [(4, self.region.id)]
        self.partner = self.env['res.partner'].create({
            'name': '_Test Partner',
            'country_id': self.country.id,
        })

    def _make_doc(self, date_created=None, party_id=None):
        vals = {'name': '_TEST-'}
        if date_created:
            vals['date_created'] = date_created
        if party_id:
            vals['party_id'] = party_id
        return self.env['sis.document'].create(vals)

    def test_analysis_year_extracted_from_date(self):
        doc = self._make_doc(date_created=date(2023, 6, 15))
        self.assertEqual(doc.analysis_year, 2023)

    def test_analysis_year_is_zero_when_no_date(self):
        doc = self._make_doc()
        self.assertEqual(doc.analysis_year, 0)

    def test_analysis_region_id_from_first_country_group(self):
        doc = self._make_doc(date_created=date(2024, 1, 1), party_id=self.partner.id)
        self.assertEqual(doc.analysis_region_id, self.region)

    def test_analysis_region_id_false_when_partner_has_no_country(self):
        partner_no_country = self.env['res.partner'].create({'name': '_No Country'})
        doc = self._make_doc(date_created=date(2024, 1, 1), party_id=partner_no_country.id)
        self.assertFalse(doc.analysis_region_id)

    def test_analysis_region_id_false_when_no_party(self):
        doc = self._make_doc(date_created=date(2024, 1, 1))
        self.assertFalse(doc.analysis_region_id)

    def test_analysis_country_id_related_to_partner_country(self):
        doc = self._make_doc(date_created=date(2024, 1, 1), party_id=self.partner.id)
        self.assertEqual(doc.analysis_country_id, self.country)

    def test_analysis_country_id_false_when_no_party(self):
        doc = self._make_doc(date_created=date(2024, 1, 1))
        self.assertFalse(doc.analysis_country_id)
```

- [ ] **Step 2.2: Run tests — verify they fail (fields not yet defined)**

```bash
docker compose exec odoo odoo -d rubicon -u sis_analysis --test-enable --stop-after-init 2>&1 | grep -E "(FAIL|ERROR|test_analysis)"
```

Expected: `AttributeError: 'sis.document' object has no attribute 'analysis_year'` or similar — confirms the test targets missing code.

- [ ] **Step 2.3: Commit the failing tests**

```bash
git add rubicon_addons/sis_analysis/tests/test_analysis_fields.py
git commit -m "test(sis_analysis): add failing tests for computed analysis fields"
```

---

## Task 3: Implement Computed Fields

**Files:**
- Modify: `rubicon_addons/sis_analysis/models/sis_document_analysis.py`

- [ ] **Step 3.1: Replace the stub with the full implementation**

```python
from odoo import models, fields, api


class SisDocumentAnalysis(models.Model):
    _inherit = 'sis.document'

    analysis_year = fields.Integer(
        string='Year',
        compute='_compute_analysis_year',
        store=True,
        depends=['date_created'],
    )
    analysis_region_id = fields.Many2one(
        'res.country.group',
        string='Region',
        compute='_compute_analysis_region',
        store=True,
        depends=['party_id.country_id.country_group_ids'],
    )
    analysis_country_id = fields.Many2one(
        'res.country',
        string='Country',
        related='party_id.country_id',
        store=True,
    )

    @api.depends('date_created')
    def _compute_analysis_year(self):
        for rec in self:
            rec.analysis_year = rec.date_created.year if rec.date_created else 0

    @api.depends('party_id.country_id.country_group_ids')
    def _compute_analysis_region(self):
        for rec in self:
            groups = rec.party_id.country_id.country_group_ids
            rec.analysis_region_id = groups[0] if groups else False
```

- [ ] **Step 3.2: Upgrade the module and run tests — verify they pass**

```bash
docker compose exec odoo odoo -d rubicon -u sis_analysis --test-enable --stop-after-init 2>&1 | grep -E "(OK|FAIL|ERROR|test_analysis)"
```

Expected: all 7 test methods show `ok`, no FAIL or ERROR lines.

- [ ] **Step 3.3: Commit**

```bash
git add rubicon_addons/sis_analysis/models/sis_document_analysis.py
git commit -m "feat(sis_analysis): add analysis_year, analysis_region_id, analysis_country_id computed fields"
```

---

## Task 4: Analysis Views

**Files:**
- Modify: `rubicon_addons/sis_analysis/views/analysis_views.xml`

- [ ] **Step 4.1: Write the full views XML**

Replace the placeholder with:

```xml
<?xml version="1.0" encoding="utf-8"?>
<odoo>

    <!-- ============ Search ============ -->
    <record id="view_sis_analysis_search" model="ir.ui.view">
        <field name="name">sis.document.analysis.search</field>
        <field name="model">sis.document</field>
        <field name="arch" type="xml">
            <search string="Analysis">
                <field name="party_id"/>
                <field name="trade_fair_id"/>
                <separator/>
                <filter string="Sales" name="filter_sales"
                    domain="[('doc_type_id.category', '=', 'S')]"/>
                <filter string="Workshop" name="filter_workshop"
                    domain="[('doc_type_id.category', '=', 'W')]"/>
                <separator/>
                <filter string="This Year" name="this_year"
                    domain="[('date_created', '>=', (context_today() + relativedelta(day=1, month=1)).strftime('%Y-%m-%d'))]"/>
                <filter string="Last Year" name="last_year"
                    domain="[('date_created', '>=', (context_today() + relativedelta(years=-1, day=1, month=1)).strftime('%Y-%m-%d')),
                             ('date_created', '&lt;', (context_today() + relativedelta(day=1, month=1)).strftime('%Y-%m-%d'))]"/>
                <group expand="0" string="Group By">
                    <filter string="Customer" name="group_party"
                        context="{'group_by': 'party_id'}"/>
                    <filter string="Region" name="group_region"
                        context="{'group_by': 'analysis_region_id'}"/>
                    <filter string="Country" name="group_country"
                        context="{'group_by': 'analysis_country_id'}"/>
                    <filter string="Fair" name="group_fair"
                        context="{'group_by': 'trade_fair_id'}"/>
                    <filter string="Year" name="group_year"
                        context="{'group_by': 'analysis_year'}"/>
                    <filter string="Quarter" name="group_quarter"
                        context="{'group_by': 'date_created:quarter'}"/>
                    <filter string="Month" name="group_month"
                        context="{'group_by': 'date_created:month'}"/>
                </group>
            </search>
        </field>
    </record>

    <!-- ============ Pivot ============ -->
    <record id="view_sis_analysis_pivot" model="ir.ui.view">
        <field name="name">sis.document.analysis.pivot</field>
        <field name="model">sis.document</field>
        <field name="arch" type="xml">
            <pivot string="Sales Analysis">
                <field name="party_id" type="row"/>
                <field name="analysis_year" type="col"/>
                <field name="total_amount" type="measure"/>
                <field name="total_qty" type="measure"/>
                <field name="total_cost" type="measure"/>
                <field name="total_profit" type="measure"/>
            </pivot>
        </field>
    </record>

    <!-- ============ Graph ============ -->
    <record id="view_sis_analysis_graph" model="ir.ui.view">
        <field name="name">sis.document.analysis.graph</field>
        <field name="model">sis.document</field>
        <field name="arch" type="xml">
            <graph string="Sales Trend" type="bar">
                <field name="analysis_year" type="row"/>
                <field name="total_amount" type="measure"/>
            </graph>
        </field>
    </record>

    <!-- ============ List ============ -->
    <record id="view_sis_analysis_list" model="ir.ui.view">
        <field name="name">sis.document.analysis.list</field>
        <field name="model">sis.document</field>
        <field name="arch" type="xml">
            <list string="Documents">
                <field name="name"/>
                <field name="party_id"/>
                <field name="analysis_year"/>
                <field name="analysis_region_id"/>
                <field name="analysis_country_id"/>
                <field name="trade_fair_id"/>
                <field name="total_qty"/>
                <field name="total_amount"/>
                <field name="total_cost"/>
                <field name="total_profit"/>
            </list>
        </field>
    </record>

    <!-- ============ Action ============ -->
    <record id="action_sis_analysis" model="ir.actions.act_window">
        <field name="name">Analysis</field>
        <field name="res_model">sis.document</field>
        <field name="view_mode">pivot,graph,list</field>
        <field name="search_view_id" ref="view_sis_analysis_search"/>
        <field name="view_ids" eval="[(5, 0, 0),
            (0, 0, {'view_mode': 'pivot', 'view_id': ref('view_sis_analysis_pivot')}),
            (0, 0, {'view_mode': 'graph', 'view_id': ref('view_sis_analysis_graph')}),
            (0, 0, {'view_mode': 'list',  'view_id': ref('view_sis_analysis_list')})]"/>
        <field name="context">{'search_default_filter_sales': 1}</field>
    </record>

</odoo>
```

- [ ] **Step 4.2: Upgrade and verify no XML errors**

```bash
docker compose exec odoo odoo -d rubicon -u sis_analysis --stop-after-init 2>&1 | grep -iE "(error|warning.*sis_analysis)"
```

Expected: no output (zero errors or warnings from `sis_analysis`).

- [ ] **Step 4.3: Commit**

```bash
git add rubicon_addons/sis_analysis/views/analysis_views.xml
git commit -m "feat(sis_analysis): add pivot, graph, list, and search views"
```

---

## Task 5: Menu Entry

**Files:**
- Modify: `rubicon_addons/sis_analysis/views/menus.xml`

- [ ] **Step 5.1: Write the menu XML**

Replace the placeholder with:

```xml
<?xml version="1.0" encoding="utf-8"?>
<odoo>

    <menuitem
        id="menu_sis_analysis"
        name="Analysis"
        parent="sis_document.menu_sis_document_root"
        action="action_sis_analysis"
        sequence="50"/>

</odoo>
```

- [ ] **Step 5.2: Upgrade and verify no errors**

```bash
docker compose exec odoo odoo -d rubicon -u sis_analysis --stop-after-init 2>&1 | grep -iE "(error|warning.*sis_analysis)"
```

Expected: no output.

- [ ] **Step 5.3: Commit**

```bash
git add rubicon_addons/sis_analysis/views/menus.xml
git commit -m "feat(sis_analysis): add Analysis menu entry under SIS Document"
```

---

## Task 6: Final Verification

- [ ] **Step 6.1: Run all sis_analysis tests one last time**

```bash
docker compose exec odoo odoo -d rubicon -u sis_analysis --test-enable --stop-after-init 2>&1 | grep -E "(Ran|OK|FAIL|ERROR)"
```

Expected: `Ran 7 tests in ...` and `OK`.

- [ ] **Step 6.2: Manual smoke test in browser**

Open `http://localhost:8069/web` and navigate to:
**SIS Document → Analysis**

Verify:
1. The pivot opens with rows = customers, columns = years, values = `total_amount`
2. "Sales" filter is pre-applied (search bar shows "Sales" chip)
3. Switching measures (top-right dropdown in pivot) shows qty, cost, profit options
4. Group By → Region groups rows by `res.country.group`
5. Group By → Fair groups rows by trade fair
6. The XLSX export button (download icon in pivot toolbar) generates a file
7. Clicking the graph icon shows the bar chart
8. Clicking a pivot cell drills down into the list view

- [ ] **Step 6.3: Final commit (if any minor fixes made during smoke test)**

```bash
git add -p
git commit -m "fix(sis_analysis): smoke test corrections"
```

---

## Notes

- **`analysis_region_id` picks the first `res.country.group`** for a given country. If a country belongs to multiple groups (e.g., France in both "Europe" and "EU"), the first group in the M2M order is used. This is deterministic but depends on the order `res.country.group` records appear. If ordering matters, add a `sequence` or `name`-based sort in `_compute_analysis_region`.

- **`search_default_filter_sales`** pre-applies the Sales filter on open. Remove from context if you want all documents shown by default.

- **No security file needed** — `sis.document` already has access rules in `sis_document`. Since `sis_analysis` adds fields via `_inherit` (no new `_name`), no new `ir.model.access` entry is required.
