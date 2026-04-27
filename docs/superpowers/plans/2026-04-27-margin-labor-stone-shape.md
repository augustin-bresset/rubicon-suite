# Margin Labor Simplification + Stone Shape Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the redundant 6-row `pdp.margin.labor` table with two Float fields on `pdp.margin` (`labor_metal_rate`, `labor_stone_rate`), and add a `stone_shape_id` dimension to `pdp.margin.stone` with most-specific-match fallback logic.

**Architecture:** Changes touch three layers in sequence: (1) the `pdp_margin` data model, (2) the `pdp_price` computation engine that reads margin rates, and (3) the `pdp_frontend` OWL workspace UI. The import script (`raw_to_data_margin.py`) is updated last, independently. Each layer is independently testable.

**Tech Stack:** Odoo 18, Python models, OWL 2 (JS/XML), pytest via `odoo-bin test`.

---

## File Map

| File | Action | What changes |
|------|--------|--------------|
| `rubicon_addons/pdp_margin/models/margin.py` | Modify | Add `labor_metal_rate`, `labor_stone_rate` Float fields |
| `rubicon_addons/pdp_margin/models/margin_stone.py` | Modify | Add `stone_shape_id` Many2one field |
| `rubicon_addons/pdp_margin/models/margin_labor.py` | Delete | Model no longer needed |
| `rubicon_addons/pdp_margin/models/__init__.py` | Modify | Remove `MarginLabor` import |
| `rubicon_addons/pdp_margin/security/ir.model.access.csv` | Modify | Remove `pdp_margin_labor` row |
| `rubicon_addons/pdp_margin/views/pdp_views.xml` | Modify | Remove labor view; add shape to stone view |
| `rubicon_addons/pdp_price/wizard/component_labor.py` | Modify | Read `margin.labor_metal_rate` / `labor_stone_rate` |
| `rubicon_addons/pdp_price/wizard/component_stone.py` | Modify | Add 4-dimension fallback stone margin lookup |
| `rubicon_addons/pdp_price/tests/test_component_labor.py` | Modify | Replace `pdp.margin.labor` helper with direct rate fields |
| `rubicon_addons/pdp_price/tests/test_component_stone.py` | Modify | Add shape-based fallback tests |
| `rubicon_addons/pdp_frontend/static/src/js/pdp_workspace.js` | Modify | Replace labor table with 2 rate fields; add shape to stone normal |
| `rubicon_addons/pdp_frontend/static/src/xml/pdp_workspace.xml` | Modify | Same as above, template side |
| `rubicon_addons/rubicon_import/raw_to_data/raw_to_data_margin.py` | Modify | Extract labor_metal/stone rates; extract stone shape |

---

## Task 1: Model changes — `pdp_margin`

**Files:**
- Modify: `rubicon_addons/pdp_margin/models/margin.py`
- Modify: `rubicon_addons/pdp_margin/models/margin_stone.py`
- Delete: `rubicon_addons/pdp_margin/models/margin_labor.py`
- Modify: `rubicon_addons/pdp_margin/models/__init__.py`
- Modify: `rubicon_addons/pdp_margin/security/ir.model.access.csv`
- Modify: `rubicon_addons/pdp_margin/views/pdp_views.xml`

- [ ] **Step 1: Add labor rate fields to `pdp.margin`**

Replace entire `rubicon_addons/pdp_margin/models/margin.py`:

```python
from odoo import fields, models


class Margin(models.Model):
    _name = "pdp.margin"
    _description = "Margin Name"
    _rec_name = "code"

    code = fields.Char(string="Margin Code", required=True, index=True)
    name = fields.Char(string="Margin Name", required=True)
    labor_metal_rate = fields.Float(
        string="Metal Labor Rate",
        digits=(5, 3),
        default=1.0,
    )
    labor_stone_rate = fields.Float(
        string="Stone Labor Rate",
        digits=(5, 3),
        default=1.0,
    )
```

- [ ] **Step 2: Add `stone_shape_id` to `pdp.margin.stone`**

Replace entire `rubicon_addons/pdp_margin/models/margin_stone.py`:

```python
from odoo import fields, models


class MarginStone(models.Model):
    _name = "pdp.margin.stone"
    _description = "Stone Margin"

    margin_id = fields.Many2one(
        string="Margin Code",
        comodel_name="pdp.margin",
        required=True,
        index=True,
        ondelete="cascade",
    )
    stone_type_id = fields.Many2one(
        string="Stone Type",
        comodel_name="pdp.stone.type",
        index=True,
    )
    stone_shape_id = fields.Many2one(
        string="Shape",
        comodel_name="pdp.stone.shape",
        index=True,
    )
    stone_size_id = fields.Many2one(
        string="Size",
        comodel_name="pdp.stone.size",
        index=True,
    )
    stone_shade_id = fields.Many2one(
        string="Shade",
        comodel_name="pdp.stone.shade",
        index=True,
    )
    rate = fields.Float(
        string="Factor, e.g. 1.10 for 10%",
        digits=(5, 3),
        required=True,
    )
```

Note: `stone_type_id` was `required=True` before; it is now optional (None = wildcard for all types).

- [ ] **Step 3: Remove `margin_labor.py`**

Delete the file:
```bash
rm rubicon_addons/pdp_margin/models/margin_labor.py
```

- [ ] **Step 4: Update `models/__init__.py`**

Replace `rubicon_addons/pdp_margin/models/__init__.py`:

```python
from .margin import Margin
from .margin_metal import MarginMetal
from .margin_stone import MarginStone
from .margin_addon import MarginAddon
from .margin_part import MarginPart
from .margin_stone_conditional import MarginStoneConditional
```

- [ ] **Step 5: Remove labor row from security CSV**

Replace `rubicon_addons/pdp_margin/security/ir.model.access.csv`:

```csv
id,name,model_id:id,group_id:id,perm_read,perm_write,perm_create,perm_unlink
pdp_margin.access_pdp_margin,access_pdp_margin,pdp_margin.model_pdp_margin,base.group_user,1,1,1,1
pdp_margin.access_pdp_margin_addon,access_pdp_margin_addon,pdp_margin.model_pdp_margin_addon,base.group_user,1,1,1,1
pdp_margin.access_pdp_margin_stone,access_pdp_margin_stone,pdp_margin.model_pdp_margin_stone,base.group_user,1,1,1,1
pdp_margin.access_pdp_margin_metal,access_pdp_margin_metal,pdp_margin.model_pdp_margin_metal,base.group_user,1,1,1,1
pdp_margin.access_pdp_margin_part,access_pdp_margin_part,pdp_margin.model_pdp_margin_part,base.group_user,1,1,1,1
pdp_margin.access_pdp_margin_stone_conditional,access_pdp_margin_stone_conditional,pdp_margin.model_pdp_margin_stone_conditional,base.group_user,1,1,1,1
```

- [ ] **Step 6: Update views — remove labor view, add shape to stone view, add labor rates to margin list**

Replace `rubicon_addons/pdp_margin/views/pdp_views.xml`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<odoo>

  <!-- Margin (with labor rates) -->
  <record id="view_pdp_margin_list" model="ir.ui.view">
    <field name="name">pdp.margin.list</field>
    <field name="model">pdp.margin</field>
    <field name="arch" type="xml">
      <list string="Margins">
        <field name="code"/>
        <field name="name"/>
        <field name="labor_metal_rate"/>
        <field name="labor_stone_rate"/>
      </list>
    </field>
  </record>

  <!-- Margin Addon -->
  <record id="view_pdp_margin_addon_list" model="ir.ui.view">
    <field name="name">pdp.margin.addon.list</field>
    <field name="model">pdp.margin.addon</field>
    <field name="arch" type="xml">
      <list string="Margin Addon">
        <field name="margin_id"/>
        <field name="addon_id"/>
        <field name="rate"/>
      </list>
    </field>
  </record>

  <!-- Margin Stone (with shape) -->
  <record id="view_pdp_margin_stone_list" model="ir.ui.view">
    <field name="name">pdp.margin.stone.list</field>
    <field name="model">pdp.margin.stone</field>
    <field name="arch" type="xml">
      <list string="Margin Stone">
        <field name="margin_id"/>
        <field name="stone_type_id"/>
        <field name="stone_shape_id"/>
        <field name="stone_size_id"/>
        <field name="stone_shade_id"/>
        <field name="rate"/>
      </list>
    </field>
  </record>

  <!-- Margin Stone Conditional -->
  <record id="view_pdp_margin_stone_conditional_list" model="ir.ui.view">
    <field name="name">pdp.margin.stone.conditional.list</field>
    <field name="model">pdp.margin.stone.conditional</field>
    <field name="arch" type="xml">
      <list string="Margin Stone Conditional">
        <field name="margin_id"/>
        <field name="stone_cat_id"/>
        <field name="operator"/>
        <field name="comparative_cost"/>
        <field name="currency_id"/>
        <field name="rate"/>
      </list>
    </field>
  </record>

  <!-- Margin Metal -->
  <record id="view_pdp_margin_metal_list" model="ir.ui.view">
    <field name="name">pdp.margin.metal.list</field>
    <field name="model">pdp.margin.metal</field>
    <field name="arch" type="xml">
      <list string="Margin Metal">
        <field name="margin_id"/>
        <field name="metal_purity_id"/>
        <field name="rate"/>
      </list>
    </field>
  </record>

  <!-- Margin Part -->
  <record id="view_pdp_margin_part_list" model="ir.ui.view">
    <field name="name">pdp.margin.part.list</field>
    <field name="model">pdp.margin.part</field>
    <field name="arch" type="xml">
      <list string="Margin part">
        <field name="margin_id"/>
        <field name="rate"/>
      </list>
    </field>
  </record>

</odoo>
```

- [ ] **Step 7: Upgrade and verify module loads**

```bash
docker compose exec odoo odoo -d rubicon -u pdp_margin --stop-after-init 2>&1 | grep -E "ERROR|WARNING|loaded"
```

Expected: No ERROR lines; module loads cleanly.

- [ ] **Step 8: Commit**

```bash
git add rubicon_addons/pdp_margin/
git commit -m "feat(pdp_margin): add labor_metal/stone_rate fields; add stone shape; remove margin_labor model"
```

---

## Task 2: Price computation — `component_labor.py`

**Files:**
- Modify: `rubicon_addons/pdp_price/wizard/component_labor.py`
- Modify: `rubicon_addons/pdp_price/tests/test_component_labor.py`

- [ ] **Step 1: Update `test_component_labor.py` — remove labor helper, update margin tests**

Replace the `_create_margin_labor_rate` helper and update the two tests that use it. In `rubicon_addons/pdp_price/tests/test_component_labor.py`:

Remove the entire `_create_margin_labor_rate` helper method (lines 80–89).

Replace `test_04_margin_applied_per_type_multiplicative`:

```python
def test_04_metal_labor_uses_labor_metal_rate(self):
    """CAS and POL both use margin.labor_metal_rate."""
    t1 = self._create_labor_type(code='CAS')
    t2 = self._create_labor_type(code='POL')
    self._create_model_cost(t1, 10.0, self.cur)
    self._create_model_cost(t2, 20.0, self.cur)
    self.margin.write({'labor_metal_rate': 1.25})

    payload = self.wizard.compute(
        product=self.product, margin=self.margin, currency=self.cur, date=fields.Date.today()
    )
    # margin = (1.25-1)*10 + (1.25-1)*20 = 2.5 + 5 = 7.5
    self.assertEqual(payload['cost'], 30.0)
    self.assertAlmostEqual(payload['margin'], 7.5, places=6)
    self.assertAlmostEqual(payload['price'], 37.5, places=6)

def test_04b_stone_labor_uses_labor_stone_rate(self):
    """REC uses margin.labor_stone_rate."""
    t = self._create_labor_type(code='REC')
    self._create_model_cost(t, 15.0, self.cur)
    self.margin.write({'labor_stone_rate': 1.40})

    payload = self.wizard.compute(
        product=self.product, margin=self.margin, currency=self.cur, date=fields.Date.today()
    )
    # margin = (1.40-1)*15 = 6.0
    self.assertEqual(payload['cost'], 15.0)
    self.assertAlmostEqual(payload['margin'], 6.0, places=6)
    self.assertAlmostEqual(payload['price'], 21.0, places=6)
```

Replace `test_07_set_margin_applied_to_setting_cost`:

```python
def test_07_set_margin_applied_to_setting_cost(self):
    """SET uses margin.labor_stone_rate (stone labor category)."""
    self._setup_stone_composition([(100.0, 2)])  # cost = 200.0
    self.margin.write({'labor_stone_rate': 1.25})

    payload = self.wizard.compute(
        product=self.product, margin=self.margin, currency=self.cur, date=fields.Date.today()
    )
    self.assertEqual(payload['cost'], 200.0)
    self.assertAlmostEqual(payload['margin'], 50.0, places=6)   # (1.25-1) × 200
    self.assertAlmostEqual(payload['price'], 250.0, places=6)
```

- [ ] **Step 2: Run tests to verify they fail (labor model missing)**

```bash
docker compose exec odoo odoo-bin test -d rubicon --test-tags pdp_price.TestPriceLabor 2>&1 | tail -20
```

Expected: FAIL — tests referencing `pdp.margin.labor` or `_create_margin_labor_rate` error out.

- [ ] **Step 3: Update `component_labor.py`**

Replace the entire file `rubicon_addons/pdp_price/wizard/component_labor.py`:

```python
from odoo import models, api

_STONE_LABOR_CODES = frozenset({'REC', 'SET'})


class PriceLabor(models.TransientModel):
    _name = 'pdp.price.labor'
    _description = 'Labor Price Component'
    _inherit = "pdp.price.component"

    @api.model
    def compute(self, *, product, margin, currency, date):
        setting_pl, labor_pl = self.compute_split(
            product=product, margin=margin, currency=currency, date=date
        )
        combined_cost = setting_pl['cost'] + labor_pl['cost']
        combined_margin = setting_pl['margin'] + labor_pl['margin']
        return self._payload('labor', combined_cost, combined_margin, currency)

    @api.model
    def compute_split(self, *, product, margin, currency, date):
        """Return (setting_payload, labor_payload) as two separate dicts."""
        clean_ctx = {k: v for k, v in self.env.context.items()
                     if not str(k).startswith('search_default_')}

        # SET (setting) is computed from stone lines, not from labor cost tables
        set_type = self.env['pdp.labor.type'].search([('code', '=', 'SET')], limit=1)

        # --- Pre-fetch all relevant costs in 2 bulk queries ---
        model_lines = self.env['pdp.labor.cost.model'].with_context(clean_ctx).search([
            ('model_id', '=', product.model_id.id)
        ])
        model_cost_by_labor = {r.labor_id.id: r for r in model_lines}

        product_lines = self.env['pdp.labor.cost.product'].with_context(clean_ctx).search([
            ('product_id', '=', product.id)
        ])
        product_cost_by_labor = {r.labor_id.id: r for r in product_lines}

        all_labor_ids = set(model_cost_by_labor) | set(product_cost_by_labor)
        has_setting = bool(set_type and product.stone_composition_id)

        # --- Build margin rate lookup from the two fields on pdp.margin ---
        margin_rate_by_labor = {}
        if margin and (all_labor_ids or has_setting):
            metal_rate = margin.labor_metal_rate or 1.0
            stone_rate = margin.labor_stone_rate or 1.0
            all_needed_ids = all_labor_ids | ({set_type.id} if set_type else set())
            for lt in self.env['pdp.labor.type'].browse(list(all_needed_ids)):
                margin_rate_by_labor[lt.id] = (
                    stone_rate if lt.code in _STONE_LABOR_CODES else metal_rate
                )

        # --- Setting cost: sum from stone lines ---
        setting_cost = setting_margin = 0.0
        if has_setting:
            stone_lines = self.env['pdp.product.stone'].with_context(clean_ctx).search([
                ('composition_id', '=', product.stone_composition_id.id)
            ])
            for sl in stone_lines:
                unit = sl.setting or 0.0
                if unit > 0.0:
                    from_cur = (sl.setting_type_id.currency_id
                                if sl.setting_type_id and sl.setting_type_id.currency_id
                                else currency)
                    setting_cost += self._convert(unit, from_cur, currency, date) * (sl.pieces or 1)
            if setting_cost:
                set_rate = margin_rate_by_labor.get(set_type.id, 1.0)
                setting_margin = (set_rate - 1.0) * setting_cost

        # --- Regular labor cost (exclude SET to avoid double-counting) ---
        all_labor_ids.discard(set_type.id if set_type else None)
        labor_cost = labor_margin = 0.0
        for labor_id in all_labor_ids:
            model_line = model_cost_by_labor.get(labor_id)
            product_line = product_cost_by_labor.get(labor_id)

            model_c = self._convert(model_line.cost, model_line.currency_id, currency, date) if model_line else 0.0
            product_c = self._convert(product_line.cost, product_line.currency_id, currency, date) if product_line else 0.0

            cost = product_c if product_c > 0.0 else model_c
            labor_cost += cost
            labor_margin += (margin_rate_by_labor.get(labor_id, 1.0) - 1.0) * cost

        setting_payload = self._payload('setting', setting_cost, setting_margin, currency)
        labor_payload = self._payload('labor', labor_cost, labor_margin, currency)
        return setting_payload, labor_payload
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
docker compose exec odoo odoo-bin test -d rubicon --test-tags pdp_price.TestPriceLabor 2>&1 | tail -20
```

Expected: all tests PASS.

- [ ] **Step 5: Commit**

```bash
git add rubicon_addons/pdp_price/wizard/component_labor.py \
        rubicon_addons/pdp_price/tests/test_component_labor.py
git commit -m "feat(pdp_price): component_labor reads labor_metal/stone_rate from pdp.margin"
```

---

## Task 3: Stone price computation — `component_stone.py`

**Files:**
- Modify: `rubicon_addons/pdp_price/wizard/component_stone.py`
- Modify: `rubicon_addons/pdp_price/tests/test_component_stone.py`

- [ ] **Step 1: Add shape-based fallback tests to `test_component_stone.py`**

Add the following two test methods to the `TestPriceStone` class in `rubicon_addons/pdp_price/tests/test_component_stone.py`:

```python
def test_compute_stone_margin_shape_exact_match(self):
    """A margin line with type+shape matches over a type-only line."""
    # Add a type+shape specific line with higher rate
    self.env['pdp.margin.stone'].create({
        'margin_id': self.margin.id,
        'stone_type_id': self.stone_type.id,
        'stone_shape_id': self.stone_shape.id,
        'rate': 1.5,  # more specific: +50%
    })
    # The existing line has type only (rate=1.2). The new line has type+shape.
    # Our stone has both type and shape set → should pick the type+shape line (1.5).
    res = self.component.compute(
        product=self.product,
        margin=self.margin,
        currency=self.currency,
        date=fields.Date.today(),
    )
    # cost=30, rate=1.5, margin=0.5*30=15
    self.assertEqual(res['cost'], self.currency.round(30.0))
    self.assertEqual(res['margin'], self.currency.round(15.0))
    self.assertEqual(res['price'], self.currency.round(45.0))

def test_compute_stone_margin_shape_fallback_to_type_only(self):
    """When no line matches the stone's shape, falls back to type-only line."""
    other_shape = self.env['pdp.stone.shape'].create({'code': 'OTH', 'shape': 'Other'})
    # Add a line for a DIFFERENT shape — should NOT match our stone
    self.env['pdp.margin.stone'].create({
        'margin_id': self.margin.id,
        'stone_type_id': self.stone_type.id,
        'stone_shape_id': other_shape.id,
        'rate': 2.0,
    })
    # Only type-only line (rate=1.2) should match our stone's shape
    res = self.component.compute(
        product=self.product,
        margin=self.margin,
        currency=self.currency,
        date=fields.Date.today(),
    )
    self.assertEqual(res['cost'], self.currency.round(30.0))
    self.assertEqual(res['margin'], self.currency.round(6.0))   # fallback: 1.2 rate
    self.assertEqual(res['price'], self.currency.round(36.0))
```

- [ ] **Step 2: Run new tests to verify they fail**

```bash
docker compose exec odoo odoo-bin test -d rubicon --test-tags pdp_price.TestPriceStone.test_compute_stone_margin_shape 2>&1 | tail -10
```

Expected: FAIL — current code ignores shape.

- [ ] **Step 3: Update `component_stone.py`**

Replace entire `rubicon_addons/pdp_price/wizard/component_stone.py`:

```python
# wizard/component_stone.py
from odoo import models, api


def _find_stone_rate(stone, margin_lines):
    """Return the most specific matching margin rate for a stone.

    A margin line matches if every non-None dimension on the line equals the
    corresponding dimension on the stone. Among all matches, the line with the
    most dimensions set wins. Returns 1.0 when no line matches.
    """
    tid  = stone.type_id.id  if stone.type_id  else False
    spid = stone.shape_id.id if stone.shape_id else False
    szid = stone.size_id.id  if stone.size_id  else False
    shid = stone.shade_id.id if stone.shade_id else False

    best_score, best_rate = -1, 1.0
    for line in margin_lines:
        if line.stone_type_id  and line.stone_type_id.id  != tid:  continue
        if line.stone_shape_id and line.stone_shape_id.id != spid: continue
        if line.stone_size_id  and line.stone_size_id.id  != szid: continue
        if line.stone_shade_id and line.stone_shade_id.id != shid: continue
        score = (
            bool(line.stone_type_id) +
            bool(line.stone_shape_id) +
            bool(line.stone_size_id) +
            bool(line.stone_shade_id)
        )
        if score > best_score:
            best_score = score
            best_rate = line.rate or 1.0
    return best_rate


class PriceStone(models.TransientModel):
    _name = 'pdp.price.stone'
    _description = 'Stone Price Component'
    _inherit = 'pdp.price.component'

    @api.model
    def compute(self, *, product, margin, currency, date):

        if not product.stone_composition_id:
            return self._payload('stone', 0.0, 0.0, currency)

        clean_ctx = {k: v for k, v in self.env.context.items()
                     if not str(k).startswith('search_default_')}

        StoneLine = self.env['pdp.product.stone'].with_context(clean_ctx)
        lines = StoneLine.search([('composition_id', '=', product.stone_composition_id.id)])

        if not lines:
            return self._payload('stone', 0.0, 0.0, currency)

        # --- Pre-fetch to warm Odoo's ORM cache (avoids N+1 on field access) ---
        stones = lines.mapped('stone_id')
        stones.mapped('type_id').mapped('category_id')

        # --- Pre-fetch ALL normal margin lines for this margin (one query) ---
        stone_margin_lines = []
        if margin:
            stone_margin_lines = self.env['pdp.margin.stone'].with_context(clean_ctx).search([
                ('margin_id', '=', margin.id),
            ])

        # --- Pre-fetch conditional margins by category (1 query) ---
        cond_by_cat = {}
        if margin:
            cat_ids = stones.mapped('type_id.category_id').ids
            if cat_ids:
                cond_lines = self.env['pdp.margin.stone.conditional'].with_context(clean_ctx).search([
                    ('margin_id', '=', margin.id),
                    ('stone_cat_id', 'in', cat_ids),
                ])
                cond_by_cat = {r.stone_cat_id.id: r for r in cond_lines}

        total_cost = total_margin = 0.0
        warnings = []

        for line in lines:
            stone = line.stone_id
            if not stone:
                continue

            from_cur = stone.currency_id or currency
            raw_cost = stone.cost or 0.0
            if raw_cost <= 0.0:
                warnings.append(f"Stone {stone.code} has no cost defined.")

            unit_cost = self._convert(raw_cost, from_cur, currency, date)
            cost = unit_cost * (line.pieces or 1.0)
            total_cost += cost

            # Conditional margin takes priority when its condition is met
            rate = 0.0
            if margin:
                cat_id = stone.type_id.category_id.id if stone.type_id and stone.type_id.category_id else False
                cond = cond_by_cat.get(cat_id)
                if cond:
                    comparative_cost = self._convert(
                        cond.comparative_cost,
                        cond.currency_id or currency,
                        currency,
                        date,
                    )
                    if cond.use_operator(cost, comparative_cost, cond.operator):
                        rate = cond.rate

            if rate == 0.0:
                rate = _find_stone_rate(stone, stone_margin_lines)

            total_margin += (rate - 1.0) * cost

        return self._payload('stone', total_cost, total_margin, currency, warnings=warnings)
```

- [ ] **Step 4: Run all stone tests**

```bash
docker compose exec odoo odoo-bin test -d rubicon --test-tags pdp_price.TestPriceStone 2>&1 | tail -20
```

Expected: all tests PASS including the two new shape tests.

- [ ] **Step 5: Commit**

```bash
git add rubicon_addons/pdp_price/wizard/component_stone.py \
        rubicon_addons/pdp_price/tests/test_component_stone.py
git commit -m "feat(pdp_price): component_stone uses 4-dimension fallback for stone margin lookup"
```

---

## Task 4: PDP Frontend — JS and XML

**Files:**
- Modify: `rubicon_addons/pdp_frontend/static/src/js/pdp_workspace.js`
- Modify: `rubicon_addons/pdp_frontend/static/src/xml/pdp_workspace.xml`

### 4a — JavaScript changes

- [ ] **Step 1: Update `state` — replace `marginLabors` with two rate fields**

In `rubicon_addons/pdp_frontend/static/src/js/pdp_workspace.js`, find the state initialisation block and replace:

```javascript
            marginLabors: [],
```

With:

```javascript
            laborMetalRate: 1.0,
            laborStoneRate: 1.0,
            laborRateDirty: false,
```

- [ ] **Step 2: Update `loadMarginData` — replace labor fetch with direct field read**

Replace the entire `loadMarginData` method:

```javascript
    async loadMarginData(marginId) {
        const [marginRec, parts, addons, metals, stoneCond, stoneNorm] = await Promise.all([
            this.orm.read("pdp.margin", [marginId], ["labor_metal_rate", "labor_stone_rate"]),
            this.orm.searchRead("pdp.margin.part", [["margin_id", "=", marginId]], ["id", "rate"]),
            this.orm.searchRead("pdp.margin.addon", [["margin_id", "=", marginId]], ["id", "addon_id", "rate"]),
            this.orm.searchRead("pdp.margin.metal", [["margin_id", "=", marginId]], ["id", "metal_purity_id", "rate"]),
            this.orm.searchRead("pdp.margin.stone.conditional", [["margin_id", "=", marginId]], ["id", "stone_cat_id", "operator", "comparative_cost", "currency_id", "rate"]),
            this.orm.searchRead("pdp.margin.stone", [["margin_id", "=", marginId]], ["id", "stone_type_id", "stone_shape_id", "stone_size_id", "stone_shade_id", "rate"]),
        ]);
        const mr = marginRec[0] || {};
        this.state.laborMetalRate = mr.labor_metal_rate || 1.0;
        this.state.laborStoneRate = mr.labor_stone_rate || 1.0;
        this.state.laborRateDirty = false;
        this.state.marginPartRecord = parts.length ? { ...parts[0], _dirty: false } : { id: null, rate: 1.0, _dirty: false };
        this.state.marginAddons = addons.map(r => ({ ...r, _key: r.id, _dirty: false }));
        this.state.marginMetals = metals.map(r => ({ ...r, _key: r.id, _dirty: false }));
        this.state.marginStonesConditional = stoneCond.map(r => ({ ...r, _key: r.id, _dirty: false }));
        this.state.marginStonesNormal = stoneNorm.map(r => ({ ...r, _key: r.id, _dirty: false }));
        this._mDelAddonIds = [];
        this._mDelMetalIds = []; this._mDelStoneCondIds = []; this._mDelStoneNormIds = [];
    }
```

- [ ] **Step 3: Replace labor helper methods with two rate setters**

Remove these three methods entirely:
- `addMarginLabor()` (lines ~1697–1699)
- `removeMarginLabor(key)` (lines ~1700–1705)
- `setMarginLaborField(key, field, value)` (lines ~1707–1712)

Add in their place:

```javascript
    setLaborMetalRate(value) {
        this.state.laborMetalRate = parseFloat(value) || 1.0;
        this.state.laborRateDirty = true;
    }
    setLaborStoneRate(value) {
        this.state.laborStoneRate = parseFloat(value) || 1.0;
        this.state.laborRateDirty = true;
    }
```

- [ ] **Step 4: Update `addMarginStoneNorm` — include shape/size/shade**

Replace:
```javascript
    addMarginStoneNorm() {
        this.state.marginStonesNormal.push({ id: null, _key: -Date.now(), _dirty: true, stone_type_id: false, rate: 1.0 });
    }
```

With:
```javascript
    addMarginStoneNorm() {
        this.state.marginStonesNormal.push({
            id: null, _key: -Date.now(), _dirty: true,
            stone_type_id: false, stone_shape_id: false,
            stone_size_id: false, stone_shade_id: false,
            rate: 1.0,
        });
    }
```

- [ ] **Step 5: Update `saveMarginData` — replace labor block, include stone shape fields**

In `saveMarginData`, replace the labor block:

```javascript
            // Labor (was pdp.margin.labor; now two fields on pdp.margin)
            if (this.state.laborRateDirty) {
                await this.orm.write("pdp.margin", [mid], {
                    labor_metal_rate: this.state.laborMetalRate,
                    labor_stone_rate: this.state.laborStoneRate,
                });
                this.state.laborRateDirty = false;
            }
```

Replace the stone normal save block:
```javascript
            // Stone Normal
            for (const r of this.state.marginStonesNormal) {
                if (!r._dirty) continue;
                const v = {
                    stone_type_id:  this.m2oId(r.stone_type_id)  || false,
                    stone_shape_id: this.m2oId(r.stone_shape_id) || false,
                    stone_size_id:  this.m2oId(r.stone_size_id)  || false,
                    stone_shade_id: this.m2oId(r.stone_shade_id) || false,
                    rate: r.rate,
                };
                if (r.id) await this.orm.write("pdp.margin.stone", [r.id], v);
                else { const [nid] = await this.orm.create("pdp.margin.stone", [{ ...v, margin_id: mid }]); r.id = nid; r._key = nid; }
                r._dirty = false;
            }
```

Also remove `this._mDelLaborIds = [];` from the delete block at the top of `saveMarginData`.

- [ ] **Step 6: Update copy margin — replace labor copy with rate copy, add shape fields to stone copy**

In the copy margin section, replace the "Copy Labors" block:

```javascript
                // Copy Labor rates (fields on pdp.margin, not a separate table)
                const srcMarginRec = await this.orm.read("pdp.margin", [srcId], ["labor_metal_rate", "labor_stone_rate"]);
                if (srcMarginRec.length) {
                    await this.orm.write("pdp.margin", [newId], {
                        labor_metal_rate: srcMarginRec[0].labor_metal_rate,
                        labor_stone_rate: srcMarginRec[0].labor_stone_rate,
                    });
                }
```

Replace the "Copy Stone Normal" block:

```javascript
                // Copy Stone Normal
                const snRules = await this.orm.searchRead("pdp.margin.stone", [["margin_id", "=", srcId]], ["stone_type_id", "stone_shape_id", "stone_size_id", "stone_shade_id", "rate"]);
                if (snRules.length) {
                    await this.orm.create("pdp.margin.stone", snRules.map(r => ({
                        margin_id: newId,
                        stone_type_id:  r.stone_type_id  ? r.stone_type_id[0]  : false,
                        stone_shape_id: r.stone_shape_id ? r.stone_shape_id[0] : false,
                        stone_size_id:  r.stone_size_id  ? r.stone_size_id[0]  : false,
                        stone_shade_id: r.stone_shade_id ? r.stone_shade_id[0] : false,
                        rate: r.rate,
                    })));
                }
```

### 4b — XML template changes

- [ ] **Step 7: Update Misc tab — replace labor table with two rate inputs**

In `rubicon_addons/pdp_frontend/static/src/xml/pdp_workspace.xml`, find the "Labor Rates" section (lines ~1211–1241) and replace:

```xml
                                    <div class="fw-bold small mt-3 mb-1 border-bottom pb-1">Labor Rates</div>
                                    <table class="table table-sm table-bordered mb-1" style="font-size:11px;">
                                        <thead class="bg-light"><tr><th>Labor Type</th><th style="width:70px;" class="text-end">Margin</th><th style="width:24px;"></th></tr></thead>
                                        <tbody>
                                            <t t-foreach="state.marginLabors" t-as="ml" t-key="ml._key">
                                                <tr t-attf-class="{{ ml._dirty ? 'table-warning' : '' }}">
                                                    <td>
                                                        <select class="form-select form-select-sm p-0" style="font-size:11px;"
                                                                t-on-change="(ev) => this.setMarginLaborField(ml._key, 'labor_id', ev.target.value)">
                                                            <option value="">--</option>
                                                            <t t-foreach="this.laborTypes" t-as="lt2" t-key="lt2.id">
                                                                <option t-att-value="lt2.id"
                                                                        t-att-selected="lt2.id === (Array.isArray(ml.labor_id) ? ml.labor_id[0] : ml.labor_id)">
                                                                    <t t-esc="lt2.code"/>
                                                                </option>
                                                            </t>
                                                        </select>
                                                    </td>
                                                    <td><input type="number" step="0.001" class="form-control form-control-sm p-0 text-end" style="font-size:11px;"
                                                               t-att-value="ml.rate"
                                                               t-on-change="(ev) => this.setMarginLaborField(ml._key, 'rate', ev.target.value)"/></td>
                                                    <td class="text-center"><button class="btn btn-sm btn-outline-danger py-0 px-1" style="font-size:10px;"
                                                            t-on-click="() => this.removeMarginLabor(ml._key)">✕</button></td>
                                                </tr>
                                            </t>
                                            <t t-if="state.marginLabors.length === 0">
                                                <tr><td colspan="3" class="text-muted text-center">None</td></tr>
                                            </t>
                                        </tbody>
                                    </table>
                                    <button class="btn btn-sm btn-outline-success py-0 px-2" style="font-size:11px;" t-on-click="() => this.addMarginLabor()">+ Add</button>
```

With:

```xml
                                    <div class="fw-bold small mt-3 mb-1 border-bottom pb-1">Labor Rates</div>
                                    <div class="d-flex align-items-center gap-2 mb-2">
                                        <label class="small" style="width:90px;">Metal Labor</label>
                                        <input type="number" step="0.001" class="form-control form-control-sm text-end" style="width:80px; font-size:11px;"
                                               t-att-value="state.laborMetalRate"
                                               t-on-change="(ev) => this.setLaborMetalRate(ev.target.value)"/>
                                    </div>
                                    <div class="d-flex align-items-center gap-2 mb-2">
                                        <label class="small" style="width:90px;">Stone Labor</label>
                                        <input type="number" step="0.001" class="form-control form-control-sm text-end" style="width:80px; font-size:11px;"
                                               t-att-value="state.laborStoneRate"
                                               t-on-change="(ev) => this.setLaborStoneRate(ev.target.value)"/>
                                    </div>
```

- [ ] **Step 8: Update Stone Normal table — add Shape, Size, Shade columns**

Replace the stone normal table header and row in `pdp_workspace.xml`:

Old header:
```xml
                                <thead class="bg-light"><tr><th>Stone Type</th><th>Category</th><th style="width:90px;" class="text-end">Margin</th><th style="width:24px;"></th></tr></thead>
```

New header:
```xml
                                <thead class="bg-light">
                                    <tr>
                                        <th>Stone Type</th>
                                        <th>Shape</th>
                                        <th>Size</th>
                                        <th>Shade</th>
                                        <th style="width:80px;" class="text-end">Margin</th>
                                        <th style="width:24px;"></th>
                                    </tr>
                                </thead>
```

Replace the old row content (inside the `<t t-foreach="state.marginStonesNormal"...>`) — replace the entire `<tr>`:

```xml
                                            <tr t-attf-class="{{ sn._dirty ? 'table-warning' : '' }}">
                                                <td>
                                                    <select class="form-select form-select-sm p-0" style="font-size:11px;"
                                                            t-on-change="(ev) => this.setMarginStoneNormField(sn._key, 'stone_type_id', ev.target.value)">
                                                        <option value="">All</option>
                                                        <t t-foreach="this.stoneTypes" t-as="styp" t-key="styp.id">
                                                            <option t-att-value="styp.id"
                                                                    t-att-selected="styp.id === (Array.isArray(sn.stone_type_id) ? sn.stone_type_id[0] : sn.stone_type_id)">
                                                                <t t-esc="styp.name"/>
                                                            </option>
                                                        </t>
                                                    </select>
                                                </td>
                                                <td>
                                                    <select class="form-select form-select-sm p-0" style="font-size:11px;"
                                                            t-on-change="(ev) => this.setMarginStoneNormField(sn._key, 'stone_shape_id', ev.target.value)">
                                                        <option value="">All</option>
                                                        <t t-foreach="this.stoneShapes" t-as="ssp" t-key="ssp.id">
                                                            <option t-att-value="ssp.id"
                                                                    t-att-selected="ssp.id === (Array.isArray(sn.stone_shape_id) ? sn.stone_shape_id[0] : sn.stone_shape_id)">
                                                                <t t-esc="ssp.shape"/>
                                                            </option>
                                                        </t>
                                                    </select>
                                                </td>
                                                <td>
                                                    <select class="form-select form-select-sm p-0" style="font-size:11px;"
                                                            t-on-change="(ev) => this.setMarginStoneNormField(sn._key, 'stone_size_id', ev.target.value)">
                                                        <option value="">All</option>
                                                        <t t-foreach="this.stoneSizes" t-as="ssz" t-key="ssz.id">
                                                            <option t-att-value="ssz.id"
                                                                    t-att-selected="ssz.id === (Array.isArray(sn.stone_size_id) ? sn.stone_size_id[0] : sn.stone_size_id)">
                                                                <t t-esc="ssz.name"/>
                                                            </option>
                                                        </t>
                                                    </select>
                                                </td>
                                                <td>
                                                    <select class="form-select form-select-sm p-0" style="font-size:11px;"
                                                            t-on-change="(ev) => this.setMarginStoneNormField(sn._key, 'stone_shade_id', ev.target.value)">
                                                        <option value="">All</option>
                                                        <t t-foreach="this.stoneShades" t-as="ssh" t-key="ssh.id">
                                                            <option t-att-value="ssh.id"
                                                                    t-att-selected="ssh.id === (Array.isArray(sn.stone_shade_id) ? sn.stone_shade_id[0] : sn.stone_shade_id)">
                                                                <t t-esc="ssh.shade"/>
                                                            </option>
                                                        </t>
                                                    </select>
                                                </td>
                                                <td><input type="number" step="0.001" class="form-control form-control-sm p-0 text-end" style="font-size:11px;"
                                                           t-att-value="sn.rate"
                                                           t-on-change="(ev) => this.setMarginStoneNormField(sn._key, 'rate', ev.target.value)"/></td>
                                                <td class="text-center"><button class="btn btn-sm btn-outline-danger py-0 px-1" style="font-size:10px;"
                                                        t-on-click="() => this.removeMarginStoneNorm(sn._key)">✕</button></td>
                                            </tr>
```

Also update the empty state colspan from `4` to `6`:
```xml
                                        <t t-if="state.marginStonesNormal.length === 0">
                                            <tr><td colspan="6" class="text-muted text-center">None</td></tr>
                                        </t>
```

- [ ] **Step 9: Upgrade and smoke-test in browser**

```bash
docker compose exec odoo odoo -d rubicon -u pdp_margin,pdp_price,pdp_frontend --stop-after-init && docker compose restart odoo
```

Open PDP → Manage → Margins. Verify:
- Misc tab shows "Metal Labor" and "Stone Labor" numeric inputs (not a table)
- Stone → Normal tab shows Type / Shape / Size / Shade / Margin columns
- Changing rates and saving works (no JS errors in console)

- [ ] **Step 10: Commit**

```bash
git add rubicon_addons/pdp_frontend/static/src/js/pdp_workspace.js \
        rubicon_addons/pdp_frontend/static/src/xml/pdp_workspace.xml
git commit -m "feat(pdp_frontend): replace labor table with 2 rate fields; add shape/size/shade to stone normal"
```

---

## Task 5: Import script — `raw_to_data_margin.py`

**Files:**
- Modify: `rubicon_addons/rubicon_import/raw_to_data/raw_to_data_margin.py`

- [ ] **Step 1: Update `pdp.margin` section to include labor rates**

In `raw_to_data_margin.py`, find the `pdp.margin` section and update:

```python
    if everything or "code" in sys.argv:

        model_name="pdp.margin"
        csv_name="Margins.csv"

        fieldnames=[
            "id", "code", "name", "labor_metal_rate", "labor_stone_rate"
        ]

        def row_to_dict(row):
            code = strip_code_space(row[0])
            return {
                "id": func_index(code, model_name),
                "code": code,
                "name": row[1],
                "labor_metal_rate": safe_float(row[5]),
                "labor_stone_rate": safe_float(row[7]),
            }

        raw_to_data(model_name, csv_name, fieldnames, row_to_dict, dest_folder='pdp_margin', index_auto=True)
```

- [ ] **Step 2: Remove the `pdp.margin.labor` section entirely**

Delete the entire block starting with `if everything or "labor" in sys.argv:` through `raw_to_data(model_name, csv_name, fieldnames, row_to_dict, dest_folder='pdp_margin', index_auto=True)` for the labor section.

- [ ] **Step 3: Update `pdp.margin.stone` section to extract shape**

Replace the `pdp.margin.stone` section:

```python
    if everything or "stone" in sys.argv:
        model_name="pdp.margin.stone"
        csv_name="StoneMargins.csv"
        fieldnames=[
            "id", "margin_id", "stone_type_id", "stone_shape_id",
            "stone_size_id", "stone_shade_id", "rate"
        ]

        def row_to_dict(row):
            margin_code = strip_code_space(row[0])
            stone_type_code = strip_code_space(row[2])
            # col[3] = stone_shape: "1" or "All" means wildcard (no filter)
            shape_raw = strip_code_space(row[3]) if len(row) > 3 else ''
            shape_code = '' if shape_raw in ('', '1', 'All', 'ALL') else shape_raw
            # col[4] = stone_size: "All" means wildcard
            size_raw = strip_code_space(row[4]) if len(row) > 4 else ''
            size_code = '' if size_raw in ('', 'All', 'ALL') else size_raw
            # col[5] = stone_shade: "1" means wildcard
            shade_raw = strip_code_space(row[5]) if len(row) > 5 else ''
            shade_code = '' if shade_raw in ('', '1', 'All', 'ALL') else shade_raw
            return {
                "id": func_index(f"{margin_code}_{stone_type_code}_{shape_code}_{size_code}_{shade_code}", model_name),
                "margin_id": margin_code,
                "stone_type_id": stone_type_code,
                "stone_shape_id": shape_code,
                "stone_size_id": size_code,
                "stone_shade_id": shade_code,
                "rate": float(row[6]),
            }

        raw_to_data(model_name, csv_name, fieldnames, row_to_dict, dest_folder='pdp_margin', index_auto=True)
```

- [ ] **Step 4: Regenerate CSV files**

```bash
cd rubicon_addons && python3 -m rubicon_import.raw_to_data.raw_to_data_margin
```

Expected output: CSVs regenerated. Verify `pdp_margin/data/pdp.margin.csv` has `labor_metal_rate` and `labor_stone_rate` columns. Verify `pdp_margin/data/pdp.margin.stone.csv` has `stone_shape_id` column. Verify `pdp.margin.labor.csv` is NOT regenerated.

- [ ] **Step 5: Truncate stone margins in DB and re-import**

Since stone margin IDs changed format (shape added to key), delete existing records before re-import. Run:

```bash
docker compose exec -T odoo odoo shell -d rubicon --no-http << 'EOF'
env['pdp.margin.stone'].search([]).unlink()
env.cr.commit()
print("pdp.margin.stone cleared.")
EOF
```

Then re-import margin data via the standard import mechanism for pdp_margin.

- [ ] **Step 6: Commit**

```bash
git add rubicon_addons/rubicon_import/raw_to_data/raw_to_data_margin.py \
        rubicon_addons/pdp_margin/data/
git commit -m "feat(import): update raw_to_data_margin for labor rates and stone shape"
```
