# Rubicon UOM Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create the `rubicon_uom` Odoo module with ratio-based UOM conversion, per-user display preferences, and OWL service integration — then wire it into the PDP workspace weight display.

**Architecture:** Three Python models (`rubicon.uom.category`, `rubicon.uom`, `rubicon.uom.user.pref`) with ORM constraints and conversion helpers. An OWL service (`rubicon_uom`) loads all data in one session-startup RPC and exposes `format/convert/symbol/setUserPref/resetUserPref`. The PDP workspace weight tab gains per-dimension UOM selectors.

**Tech Stack:** Odoo 18, Python ORM (`TransactionCase` tests), OWL 2 (`/** @odoo-module **/`, `registry.category("services")`), XML data files.

---

## Assumptions

- Metal weights in DB are stored in **grams** (reference unit for `metal_weight`).
- Stone weights in DB are stored in **carats** (reference unit for `stone_weight`).
- Values are never migrated — this plan only adds display conversion, not data rewriting.

---

## File Structure

### New — `rubicon_addons/rubicon_uom/`

| File | Responsibility |
|---|---|
| `__manifest__.py` | Module descriptor |
| `__init__.py` | Model imports |
| `models/__init__.py` | Model imports |
| `models/uom_category.py` | `rubicon.uom.category` incl. `uom_ids` O2M and `get_user_uom()` |
| `models/uom.py` | `rubicon.uom` with `convert()`, `set_global_default()` |
| `models/uom_user_pref.py` | `rubicon.uom.user.pref` only (no `_inherit`) |
| `data/rubicon_uom_data.xml` | Pre-populated categories + units |
| `security/ir.model.access.csv` | Access rights |
| `views/uom_views.xml` | Admin list/form views |
| `views/res_config_settings_views.xml` | Settings block with link |
| `static/src/js/rubicon_uom_service.js` | OWL service |
| `static/src/xml/rubicon_uom_selector.xml` | UOM selector template |
| `static/src/js/rubicon_uom_selector.js` | UOM selector component |
| `tests/__init__.py` | Test imports |
| `tests/test_rubicon_uom.py` | All Python tests |

### Modified

| File | Change |
|---|---|
| `pdp_frontend/__manifest__.py` | Add `rubicon_uom` dependency |
| `pdp_frontend/views/pdp_menus.xml` | Add "Units of Measure" settings menu item |
| `pdp_frontend/static/src/js/pdp_workspace.js` | Inject UOM service, convert weight display |
| `pdp_frontend/static/src/xml/pdp_workspace.xml` | Add UOM selectors in weight tab header |

---

## Task 1: Module scaffold

**Files:**
- Create: `rubicon_addons/rubicon_uom/__manifest__.py`
- Create: `rubicon_addons/rubicon_uom/__init__.py`
- Create: `rubicon_addons/rubicon_uom/models/__init__.py`
- Create: `rubicon_addons/rubicon_uom/tests/__init__.py`
- Create: `rubicon_addons/rubicon_uom/security/ir.model.access.csv`

- [ ] **Step 1: Create `__manifest__.py`**

```python
{
    'name': 'Rubicon UOM',
    'version': '0.1.0',
    'license': 'LGPL-3',
    'summary': 'Reusable unit-of-measure registry with ratio-based conversion and per-user preferences',
    'author': 'Rubicon',
    'depends': ['base'],
    'data': [
        'security/ir.model.access.csv',
        'data/rubicon_uom_data.xml',
        'views/uom_views.xml',
        'views/res_config_settings_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'rubicon_uom/static/src/**/*',
        ],
    },
    'installable': True,
    'application': False,
}
```

- [ ] **Step 2: Create `__init__.py`**

```python
from . import models
```

- [ ] **Step 3: Create `models/__init__.py`**

```python
from . import uom_category
from . import uom
from . import uom_user_pref
```

- [ ] **Step 4: Create `tests/__init__.py`**

```python
from . import test_rubicon_uom
```

- [ ] **Step 5: Create `security/ir.model.access.csv`**

```csv
id,name,model_id:id,group_id:id,perm_read,perm_write,perm_create,perm_unlink
access_rubicon_uom_category_user,rubicon.uom.category user,model_rubicon_uom_category,base.group_user,1,0,0,0
access_rubicon_uom_category_admin,rubicon.uom.category admin,model_rubicon_uom_category,base.group_system,1,1,1,1
access_rubicon_uom_user,rubicon.uom user,model_rubicon_uom,base.group_user,1,0,0,0
access_rubicon_uom_admin,rubicon.uom admin,model_rubicon_uom,base.group_system,1,1,1,1
access_rubicon_uom_user_pref_user,rubicon.uom.user.pref user,model_rubicon_uom_user_pref,base.group_user,1,1,1,1
```

---

## Task 2: `rubicon.uom.category` model

**Files:**
- Create: `rubicon_addons/rubicon_uom/models/uom_category.py`
- Create: `rubicon_addons/rubicon_uom/tests/test_rubicon_uom.py`

- [ ] **Step 1: Write the failing test**

Create `rubicon_addons/rubicon_uom/tests/test_rubicon_uom.py`:

```python
from odoo.tests.common import TransactionCase


class TestRubiconUomCategory(TransactionCase):

    def test_create_category(self):
        cat = self.env['rubicon.uom.category'].create({
            'name': 'Test Weight',
            'code': 'test_weight',
        })
        self.assertEqual(cat.code, 'test_weight')
        # _rec_name='code' means display_name == code value
        self.assertEqual(cat.display_name, 'test_weight')

    def test_code_unique(self):
        self.env['rubicon.uom.category'].create({'name': 'A', 'code': 'unique_test'})
        with self.assertRaises(Exception):
            self.env['rubicon.uom.category'].create({'name': 'B', 'code': 'unique_test'})
```

- [ ] **Step 2: Run test — expect FAIL (model does not exist)**

```bash
docker compose exec odoo odoo -d rubicon --test-enable --stop-after-init -u rubicon_uom --test-tags /rubicon_uom:TestRubiconUomCategory 2>&1 | tail -20
```

Expected: error about missing model.

- [ ] **Step 3: Create `models/uom_category.py`**

```python
from odoo import models, fields


class RubiconUomCategory(models.Model):
    _name = 'rubicon.uom.category'
    _description = 'UOM Category (dimension)'
    _rec_name = 'code'

    name = fields.Char(string='Name', required=True)
    code = fields.Char(string='Code', required=True, index=True)
    description = fields.Char(string='Description')
    # Declared here so views and get_user_uom() can reference it without _inherit tricks.
    # The inverse side (rubicon.uom.category_id) is defined in uom.py.
    uom_ids = fields.One2many('rubicon.uom', 'category_id', string='Units')

    _sql_constraints = [
        ('code_unique', 'UNIQUE(code)', 'Category code must be unique.'),
    ]

    def get_user_uom(self, user_id=None):
        """Return the active display unit for a given user.

        Fallback chain: user pref → global default → reference unit.
        Never returns False — reference unit is always present.
        """
        self.ensure_one()
        uid = user_id or self.env.uid
        pref = self.env['rubicon.uom.user.pref'].search([
            ('user_id', '=', uid),
            ('category_id', '=', self.id),
        ], limit=1)
        if pref:
            return pref.uom_id

        default = self.env['rubicon.uom'].search([
            ('category_id', '=', self.id),
            ('is_global_default', '=', True),
        ], limit=1)
        if default:
            return default

        return self.env['rubicon.uom'].search([
            ('category_id', '=', self.id),
            ('is_reference', '=', True),
        ], limit=1)
```

> **Note:** `get_user_uom()` references `rubicon.uom.user.pref` which is defined in `uom_user_pref.py`. Python import order in `models/__init__.py` must be `uom_category`, then `uom`, then `uom_user_pref` — this ensures both models are registered before the method is called at runtime (not at class-definition time), which is safe.

- [ ] **Step 4: Run test — expect PASS**

```bash
docker compose exec odoo odoo -d rubicon --test-enable --stop-after-init -u rubicon_uom --test-tags /rubicon_uom:TestRubiconUomCategory 2>&1 | tail -20
```

- [ ] **Step 5: Commit**

```bash
git add rubicon_addons/rubicon_uom/
git commit -m "feat(rubicon_uom): scaffold module + rubicon.uom.category model"
```

---

## Task 3: `rubicon.uom` model with `convert()`

**Files:**
- Create: `rubicon_addons/rubicon_uom/models/uom.py`
- Modify: `rubicon_addons/rubicon_uom/tests/test_rubicon_uom.py`

- [ ] **Step 1: Write failing tests** (append to test file)

```python
class TestRubiconUomConversion(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.cat = cls.env['rubicon.uom.category'].create({
            'name': 'Metal Weight', 'code': 'metal_weight',
        })
        cls.cat2 = cls.env['rubicon.uom.category'].create({
            'name': 'Stone Weight', 'code': 'stone_weight',
        })
        cls.gram = cls.env['rubicon.uom'].create({
            'name': 'Gramme', 'symbol': 'g',
            'category_id': cls.cat.id,
            'ratio': 1.0, 'is_reference': True, 'is_global_default': True,
        })
        cls.troy_oz = cls.env['rubicon.uom'].create({
            'name': 'Troy Ounce', 'symbol': 'oz t',
            'category_id': cls.cat.id,
            'ratio': 31.1035, 'is_reference': False, 'is_global_default': False,
        })
        cls.carat = cls.env['rubicon.uom'].create({
            'name': 'Carat', 'symbol': 'ct',
            'category_id': cls.cat2.id,
            'ratio': 1.0, 'is_reference': True, 'is_global_default': True,
        })

    def test_convert_g_to_troy_oz(self):
        result = self.gram.convert(62.207, self.troy_oz)
        self.assertAlmostEqual(result, 2.0, places=3)

    def test_convert_troy_oz_to_g(self):
        result = self.troy_oz.convert(2.0, self.gram)
        self.assertAlmostEqual(result, 62.207, places=2)

    def test_round_trip(self):
        original = 42.5
        via_troy = self.gram.convert(original, self.troy_oz)
        back = self.troy_oz.convert(via_troy, self.gram)
        self.assertAlmostEqual(back, original, places=6)

    def test_convert_zero_returns_zero(self):
        self.assertEqual(self.gram.convert(0, self.troy_oz), 0)

    def test_convert_none_returns_zero(self):
        self.assertEqual(self.gram.convert(None, self.troy_oz), 0)

    def test_convert_negative_allowed(self):
        result = self.gram.convert(-10.0, self.troy_oz)
        self.assertAlmostEqual(result, -10.0 / 31.1035, places=6)

    def test_cross_category_raises(self):
        from odoo.exceptions import UserError
        with self.assertRaises(UserError):
            self.gram.convert(10.0, self.carat)
```

- [ ] **Step 2: Run — expect FAIL**

```bash
docker compose exec odoo odoo -d rubicon --test-enable --stop-after-init -u rubicon_uom --test-tags /rubicon_uom:TestRubiconUomConversion 2>&1 | tail -20
```

- [ ] **Step 3: Create `models/uom.py`**

```python
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class RubiconUom(models.Model):
    _name = 'rubicon.uom'
    _description = 'Unit of Measure'
    _rec_name = 'symbol'
    _order = 'category_id, is_reference desc, name'

    name = fields.Char(string='Name', required=True)
    symbol = fields.Char(string='Symbol', required=True)
    category_id = fields.Many2one(
        'rubicon.uom.category', string='Category', required=True, ondelete='cascade',
    )
    ratio = fields.Float(
        string='Ratio', digits=(12, 6), default=1.0,
        help='Number of reference units in 1 of this unit. Reference unit = 1.0.',
    )
    is_reference = fields.Boolean(string='Is Reference Unit', default=False)
    is_global_default = fields.Boolean(string='Global Default', default=False)

    @api.constrains('is_reference', 'category_id')
    def _check_one_reference_per_category(self):
        for rec in self:
            if rec.is_reference:
                others = self.search([
                    ('category_id', '=', rec.category_id.id),
                    ('is_reference', '=', True),
                    ('id', '!=', rec.id),
                ])
                if others:
                    raise UserError(
                        _('Category "%s" already has a reference unit.') % rec.category_id.code
                    )

    @api.constrains('is_global_default', 'category_id')
    def _check_one_global_default_per_category(self):
        for rec in self:
            if rec.is_global_default:
                others = self.search([
                    ('category_id', '=', rec.category_id.id),
                    ('is_global_default', '=', True),
                    ('id', '!=', rec.id),
                ])
                if others:
                    raise UserError(
                        _('Category "%s" already has a global default unit.') % rec.category_id.code
                    )

    def convert(self, value, to_uom):
        """Convert value expressed in self to to_uom.

        Raises UserError if self and to_uom belong to different categories.
        Returns 0 for None, False, or zero values. Negative values are allowed.
        """
        self.ensure_one()
        if self.category_id != to_uom.category_id:
            raise UserError(
                _('Cannot convert between units of different categories (%s vs %s).')
                % (self.category_id.code, to_uom.category_id.code)
            )
        if not value:
            return 0
        return value * self.ratio / to_uom.ratio

    def set_global_default(self):
        """Atomically set this unit as the global default for its category.

        Unsets is_global_default on the current default, sets it on self.

        Note: the spec places this method on rubicon.uom.category with a uom_id
        argument. This plan places it on rubicon.uom (no argument) for simplicity.
        Both approaches are functionally equivalent. The settings UI (v1) calls
        this indirectly via the admin form view rather than programmatically.
        """
        self.ensure_one()
        current = self.search([
            ('category_id', '=', self.category_id.id),
            ('is_global_default', '=', True),
            ('id', '!=', self.id),
        ])
        current.write({'is_global_default': False})
        self.write({'is_global_default': True})
```

- [ ] **Step 4: Run — expect PASS**

```bash
docker compose exec odoo odoo -d rubicon --test-enable --stop-after-init -u rubicon_uom --test-tags /rubicon_uom:TestRubiconUomConversion 2>&1 | tail -20
```

- [ ] **Step 5: Commit**

```bash
git add rubicon_addons/rubicon_uom/
git commit -m "feat(rubicon_uom): rubicon.uom model with convert() and set_global_default()"
```

---

## Task 4: `rubicon.uom.user.pref` + `get_user_uom()`

**Files:**
- Create: `rubicon_addons/rubicon_uom/models/uom_user_pref.py`
- Modify: `rubicon_addons/rubicon_uom/tests/test_rubicon_uom.py`

- [ ] **Step 1: Write failing tests** (append to test file)

```python
class TestRubiconUomUserPref(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.cat = cls.env['rubicon.uom.category'].create({
            'name': 'Metal Weight', 'code': 'mw_pref_test',
        })
        cls.cat2 = cls.env['rubicon.uom.category'].create({
            'name': 'Stone Weight', 'code': 'sw_pref_test',
        })
        cls.gram = cls.env['rubicon.uom'].create({
            'name': 'Gramme', 'symbol': 'g', 'category_id': cls.cat.id,
            'ratio': 1.0, 'is_reference': True, 'is_global_default': True,
        })
        cls.troy_oz = cls.env['rubicon.uom'].create({
            'name': 'Troy Oz', 'symbol': 'oz t', 'category_id': cls.cat.id,
            'ratio': 31.1035, 'is_reference': False, 'is_global_default': False,
        })
        cls.carat = cls.env['rubicon.uom'].create({
            'name': 'Carat', 'symbol': 'ct', 'category_id': cls.cat2.id,
            'ratio': 1.0, 'is_reference': True, 'is_global_default': True,
        })
        cls.user = cls.env.ref('base.user_demo')

    def test_get_user_uom_returns_user_pref(self):
        self.env['rubicon.uom.user.pref'].create({
            'user_id': self.user.id,
            'category_id': self.cat.id,
            'uom_id': self.troy_oz.id,
        })
        result = self.cat.get_user_uom(user_id=self.user.id)
        self.assertEqual(result, self.troy_oz)

    def test_get_user_uom_falls_back_to_global_default(self):
        result = self.cat.get_user_uom(user_id=self.user.id)
        self.assertEqual(result, self.gram)

    def test_get_user_uom_falls_back_to_reference(self):
        # No global default — gram is reference only.
        # Safe to mutate self.gram here: Odoo TransactionCase wraps each test_*
        # method in a savepoint that is rolled back after the test, so this
        # write does not affect other test methods.
        self.gram.write({'is_global_default': False})
        result = self.cat.get_user_uom(user_id=self.user.id)
        self.assertEqual(result, self.gram)  # is_reference=True

    def test_delete_pref_reverts_to_global_default(self):
        pref = self.env['rubicon.uom.user.pref'].create({
            'user_id': self.user.id,
            'category_id': self.cat.id,
            'uom_id': self.troy_oz.id,
        })
        self.assertEqual(self.cat.get_user_uom(user_id=self.user.id), self.troy_oz)
        pref.unlink()
        self.assertEqual(self.cat.get_user_uom(user_id=self.user.id), self.gram)

    def test_uom_must_belong_to_category(self):
        from odoo.exceptions import ValidationError
        with self.assertRaises(ValidationError):
            self.env['rubicon.uom.user.pref'].create({
                'user_id': self.user.id,
                'category_id': self.cat.id,
                'uom_id': self.carat.id,  # belongs to cat2, not cat
            })

    def test_unique_per_user_category(self):
        self.env['rubicon.uom.user.pref'].create({
            'user_id': self.user.id,
            'category_id': self.cat.id,
            'uom_id': self.gram.id,
        })
        with self.assertRaises(Exception):
            self.env['rubicon.uom.user.pref'].create({
                'user_id': self.user.id,
                'category_id': self.cat.id,
                'uom_id': self.troy_oz.id,
            })

    def test_set_global_default_atomic(self):
        self.troy_oz.set_global_default()
        self.assertTrue(self.troy_oz.is_global_default)
        self.assertFalse(self.gram.is_global_default)
```

- [ ] **Step 2: Run — expect FAIL**

```bash
docker compose exec odoo odoo -d rubicon --test-enable --stop-after-init -u rubicon_uom --test-tags /rubicon_uom:TestRubiconUomUserPref 2>&1 | tail -20
```

- [ ] **Step 3: Create `models/uom_user_pref.py`**

```python
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class RubiconUomUserPref(models.Model):
    _name = 'rubicon.uom.user.pref'
    _description = 'Per-user UOM display preference'

    user_id = fields.Many2one('res.users', string='User', required=True, ondelete='cascade')
    category_id = fields.Many2one(
        'rubicon.uom.category', string='Category', required=True, ondelete='cascade',
    )
    uom_id = fields.Many2one('rubicon.uom', string='Unit', required=True, ondelete='cascade')

    _sql_constraints = [
        ('unique_user_category', 'UNIQUE(user_id, category_id)',
         'A user can only have one UOM preference per category.'),
    ]

    @api.constrains('uom_id', 'category_id')
    def _check_uom_matches_category(self):
        for rec in self:
            if rec.uom_id.category_id != rec.category_id:
                raise ValidationError(
                    _('Unit "%s" does not belong to category "%s".')
                    % (rec.uom_id.symbol, rec.category_id.code)
                )
```

> `get_user_uom()` lives in `uom_category.py` — not here. `uom_user_pref.py` contains only `RubiconUomUserPref`.

- [ ] **Step 4: Run — expect PASS**

```bash
docker compose exec odoo odoo -d rubicon --test-enable --stop-after-init -u rubicon_uom --test-tags /rubicon_uom:TestRubiconUomUserPref 2>&1 | tail -20
```

- [ ] **Step 5: Run all rubicon_uom tests**

```bash
docker compose exec odoo odoo -d rubicon --test-enable --stop-after-init -u rubicon_uom --test-tags /rubicon_uom 2>&1 | tail -30
```

- [ ] **Step 6: Commit**

```bash
git add rubicon_addons/rubicon_uom/
git commit -m "feat(rubicon_uom): rubicon.uom.user.pref + get_user_uom() fallback chain"
```

---

## Task 5: Pre-populated data + admin views

**Files:**
- Create: `rubicon_addons/rubicon_uom/data/rubicon_uom_data.xml`
- Create: `rubicon_addons/rubicon_uom/views/uom_views.xml`
- Create: `rubicon_addons/rubicon_uom/views/res_config_settings_views.xml`

- [ ] **Step 1: Create `data/rubicon_uom_data.xml`**

```xml
<?xml version="1.0" encoding="utf-8"?>
<odoo>
  <!-- Categories -->
  <record id="uom_cat_metal_weight" model="rubicon.uom.category">
    <field name="name">Metal Weight</field>
    <field name="code">metal_weight</field>
  </record>
  <record id="uom_cat_stone_weight" model="rubicon.uom.category">
    <field name="name">Stone Weight</field>
    <field name="code">stone_weight</field>
  </record>
  <record id="uom_cat_stone_density" model="rubicon.uom.category">
    <field name="name">Stone Density</field>
    <field name="code">stone_density</field>
  </record>
  <record id="uom_cat_stone_size" model="rubicon.uom.category">
    <field name="name">Stone Size</field>
    <field name="code">stone_size</field>
  </record>

  <!-- Metal Weight units -->
  <record id="uom_g" model="rubicon.uom">
    <field name="name">Gramme</field>
    <field name="symbol">g</field>
    <field name="category_id" ref="uom_cat_metal_weight"/>
    <field name="ratio">1.0</field>
    <field name="is_reference" eval="True"/>
    <field name="is_global_default" eval="True"/>
  </record>
  <record id="uom_troy_oz" model="rubicon.uom">
    <field name="name">Troy Ounce</field>
    <field name="symbol">oz t</field>
    <field name="category_id" ref="uom_cat_metal_weight"/>
    <field name="ratio">31.1035</field>
    <field name="is_reference" eval="False"/>
    <field name="is_global_default" eval="False"/>
  </record>

  <!-- Stone Weight units -->
  <record id="uom_ct" model="rubicon.uom">
    <field name="name">Carat</field>
    <field name="symbol">ct</field>
    <field name="category_id" ref="uom_cat_stone_weight"/>
    <field name="ratio">1.0</field>
    <field name="is_reference" eval="True"/>
    <field name="is_global_default" eval="True"/>
  </record>
  <record id="uom_g_stone" model="rubicon.uom">
    <field name="name">Gramme (stone)</field>
    <field name="symbol">g</field>
    <field name="category_id" ref="uom_cat_stone_weight"/>
    <field name="ratio">5.0</field>
    <field name="is_reference" eval="False"/>
    <field name="is_global_default" eval="False"/>
  </record>

  <!-- Stone Density units -->
  <record id="uom_rel_quartz" model="rubicon.uom">
    <field name="name">Relative to Quartz</field>
    <field name="symbol">×SiO₂</field>
    <field name="category_id" ref="uom_cat_stone_density"/>
    <field name="ratio">1.0</field>
    <field name="is_reference" eval="True"/>
    <field name="is_global_default" eval="True"/>
  </record>
  <record id="uom_gcm3" model="rubicon.uom">
    <field name="name">Gramme per cm³</field>
    <field name="symbol">g/cm³</field>
    <field name="category_id" ref="uom_cat_stone_density"/>
    <field name="ratio">0.377358</field>
    <field name="is_reference" eval="False"/>
    <field name="is_global_default" eval="False"/>
  </record>

  <!-- Stone Size units -->
  <record id="uom_mm" model="rubicon.uom">
    <field name="name">Millimetre</field>
    <field name="symbol">mm</field>
    <field name="category_id" ref="uom_cat_stone_size"/>
    <field name="ratio">1.0</field>
    <field name="is_reference" eval="True"/>
    <field name="is_global_default" eval="True"/>
  </record>
  <record id="uom_inch" model="rubicon.uom">
    <field name="name">Inch</field>
    <field name="symbol">in</field>
    <field name="category_id" ref="uom_cat_stone_size"/>
    <field name="ratio">25.4</field>
    <field name="is_reference" eval="False"/>
    <field name="is_global_default" eval="False"/>
  </record>
</odoo>
```

- [ ] **Step 2: Create `views/uom_views.xml`**

```xml
<?xml version="1.0" encoding="utf-8"?>
<odoo>
  <!-- rubicon.uom list (inline in category form) -->
  <record id="view_rubicon_uom_list_inline" model="ir.ui.view">
    <field name="name">rubicon.uom.list.inline</field>
    <field name="model">rubicon.uom</field>
    <field name="arch" type="xml">
      <list editable="bottom">
        <field name="name"/>
        <field name="symbol"/>
        <field name="ratio"/>
        <field name="is_reference"/>
        <field name="is_global_default"/>
      </list>
    </field>
  </record>

  <!-- rubicon.uom.category form -->
  <record id="view_rubicon_uom_category_form" model="ir.ui.view">
    <field name="name">rubicon.uom.category.form</field>
    <field name="model">rubicon.uom.category</field>
    <field name="arch" type="xml">
      <form>
        <sheet>
          <group>
            <field name="name"/>
            <field name="code"/>
            <field name="description"/>
          </group>
          <notebook>
            <page string="Units">
              <field name="uom_ids" widget="one2many_list"
                     views="[('list', 'view_rubicon_uom_list_inline')]"/>
            </page>
          </notebook>
        </sheet>
      </form>
    </field>
  </record>

  <!-- rubicon.uom.category list -->
  <record id="view_rubicon_uom_category_list" model="ir.ui.view">
    <field name="name">rubicon.uom.category.list</field>
    <field name="model">rubicon.uom.category</field>
    <field name="arch" type="xml">
      <list>
        <field name="code"/>
        <field name="name"/>
        <field name="description"/>
      </list>
    </field>
  </record>

  <!-- Action -->
  <record id="action_rubicon_uom_category" model="ir.actions.act_window">
    <field name="name">Units of Measure</field>
    <field name="res_model">rubicon.uom.category</field>
    <field name="view_mode">list,form</field>
    <field name="help" type="html">
      <p class="o_view_nocontent_smiling_face">No UOM categories yet</p>
      <p>Define measurement dimensions and their units (e.g. Metal Weight: g, oz t).</p>
    </field>
  </record>
</odoo>
```

> **Spec deviation (v1 scope reduction):** The spec calls for a dropdown per category in the settings UI that calls `set_global_default()`. This plan instead provides a link button to the admin list view. The per-category dropdown UI is deferred. Changing global defaults in v1 is done by editing the unit record directly (toggling `is_global_default` via the form view). A future task can add the dropdown-per-category settings page.

- [ ] **Step 3: Create `views/res_config_settings_views.xml`**

```xml
<?xml version="1.0" encoding="utf-8"?>
<odoo>
  <record id="res_config_settings_view_rubicon_uom" model="ir.ui.view">
    <field name="name">rubicon.uom.res.config.settings</field>
    <field name="model">res.config.settings</field>
    <field name="priority" eval="90"/>
    <field name="inherit_id" ref="base.res_config_settings_view_form"/>
    <field name="arch" type="xml">
      <xpath expr="//form" position="inside">
        <app data-string="Rubicon UOM" string="Rubicon UOM" name="rubicon_uom" groups="base.group_system">
          <block title="Units of Measure">
            <setting string="Manage UOM categories and global defaults"
                     help="Define which unit is displayed by default per measurement dimension.">
              <button name="%(rubicon_uom.action_rubicon_uom_category)d" type="action"
                      string="Open Units of Measure" class="btn-link"/>
            </setting>
          </block>
        </app>
      </xpath>
    </field>
  </record>
</odoo>
```

- [ ] **Step 4: Install module and verify data loads**

```bash
docker compose exec odoo odoo -d rubicon -u rubicon_uom --stop-after-init 2>&1 | tail -20
```

Expected: no errors, module installs cleanly.

- [ ] **Step 5: Verify in shell that 4 categories and 8 units exist**

```bash
docker compose exec odoo odoo shell -d rubicon --no-http <<'EOF'
cats = env['rubicon.uom.category'].search([])
print(f"Categories: {len(cats)}")
for c in cats:
    units = env['rubicon.uom'].search([('category_id','=',c.id)])
    print(f"  {c.code}: {[u.symbol for u in units]}")
EOF
```

Expected: 4 categories, 2 units each.

- [ ] **Step 6: Commit**

```bash
git add rubicon_addons/rubicon_uom/
git commit -m "feat(rubicon_uom): pre-populated UOM data + admin views + settings block"
```

---

## Task 6: OWL service

**Files:**
- Create: `rubicon_addons/rubicon_uom/static/src/js/rubicon_uom_service.js`

- [ ] **Step 1: Create `static/src/js/rubicon_uom_service.js`**

```js
/** @odoo-module **/

import { registry } from "@web/core/registry";

const rubiconUomService = {
    dependencies: ["orm", "user"],

    start(env, { orm, user }) {
        let _categories = [];
        let _units = [];
        let _userPrefs = {};   // { category_id: uom_id }
        let _loaded = false;

        async function load() {
            const [categories, units, prefs] = await Promise.all([
                orm.searchRead('rubicon.uom.category', [], ['name', 'code']),
                orm.searchRead('rubicon.uom', [], [
                    'name', 'symbol', 'category_id', 'ratio', 'is_reference', 'is_global_default',
                ]),
                orm.searchRead('rubicon.uom.user.pref',
                    [['user_id', '=', user.userId]],
                    ['category_id', 'uom_id']
                ),
            ]);
            _categories = categories;
            _units = units;
            _userPrefs = {};
            for (const pref of prefs) {
                const catId = Array.isArray(pref.category_id) ? pref.category_id[0] : pref.category_id;
                const uomId = Array.isArray(pref.uom_id) ? pref.uom_id[0] : pref.uom_id;
                _userPrefs[catId] = uomId;
            }
            _loaded = true;
        }

        function _catByCode(code) {
            return _categories.find(c => c.code === code);
        }

        function _uomById(id) {
            return _units.find(u => u.id === id);
        }

        function _unitsForCat(catId) {
            return _units.filter(u => {
                const cid = Array.isArray(u.category_id) ? u.category_id[0] : u.category_id;
                return cid === catId;
            });
        }

        function _activeUom(categoryCode) {
            if (!_loaded) return null;
            const cat = _catByCode(categoryCode);
            if (!cat) {
                console.warn(`[rubicon_uom] Unknown category: ${categoryCode}`);
                return null;
            }
            const catUnits = _unitsForCat(cat.id);
            // 1. user pref
            const prefId = _userPrefs[cat.id];
            if (prefId) {
                const pref = catUnits.find(u => u.id === prefId);
                if (pref) return pref;
            }
            // 2. global default
            const gd = catUnits.find(u => u.is_global_default);
            if (gd) return gd;
            // 3. reference
            return catUnits.find(u => u.is_reference) || null;
        }

        function _refUom(categoryCode) {
            if (!_loaded) return null;
            const cat = _catByCode(categoryCode);
            if (!cat) return null;
            return _unitsForCat(cat.id).find(u => u.is_reference) || null;
        }

        function convert(value, categoryCode) {
            const active = _activeUom(categoryCode);
            if (!active || !value) return value || 0;
            const ref = _refUom(categoryCode);
            if (!ref) return value;
            return value * ref.ratio / active.ratio;
        }

        function symbol(categoryCode) {
            const uom = _activeUom(categoryCode);
            return uom ? uom.symbol : '';
        }

        function format(value, categoryCode, digits = 3) {
            const sym = symbol(categoryCode);
            const val = convert(value, categoryCode);
            if (!sym) return String(value || 0);
            return `${Number(val).toFixed(digits)} ${sym}`;
        }

        function convertExplicit(value, fromUomId, toUomId) {
            const from = _uomById(fromUomId);
            const to = _uomById(toUomId);
            if (!from || !to || !value) return value || 0;
            return value * from.ratio / to.ratio;
        }

        function getUnitsForCategory(categoryCode) {
            if (!_loaded) return [];
            const cat = _catByCode(categoryCode);
            if (!cat) return [];
            return _unitsForCat(cat.id);
        }

        function getActiveUom(categoryCode) {
            return _activeUom(categoryCode);
        }

        function hasUserPref(categoryCode) {
            if (!_loaded) return false;
            const cat = _catByCode(categoryCode);
            return cat ? cat.id in _userPrefs : false;
        }

        async function setUserPref(categoryCode, uomId) {
            const cat = _catByCode(categoryCode);
            if (!cat) return;
            const existing = await orm.searchRead(
                'rubicon.uom.user.pref',
                [['user_id', '=', user.userId], ['category_id', '=', cat.id]],
                ['id']
            );
            if (existing.length) {
                await orm.unlink('rubicon.uom.user.pref', existing.map(r => r.id));
            }
            await orm.create('rubicon.uom.user.pref', [{
                user_id: user.userId,
                category_id: cat.id,
                uom_id: uomId,
            }]);
            await load();
        }

        async function resetUserPref(categoryCode) {
            const cat = _catByCode(categoryCode);
            if (!cat) return;
            const existing = await orm.searchRead(
                'rubicon.uom.user.pref',
                [['user_id', '=', user.userId], ['category_id', '=', cat.id]],
                ['id']
            );
            if (existing.length) {
                await orm.unlink('rubicon.uom.user.pref', existing.map(r => r.id));
            }
            await load();
        }

        return {
            load,
            convert,
            convertExplicit,
            symbol,
            format,
            getUnitsForCategory,
            getActiveUom,
            hasUserPref,
            setUserPref,
            resetUserPref,
        };
    },
};

registry.category("services").add("rubicon_uom", rubiconUomService);
```

- [ ] **Step 2: Install to deploy JS assets**

```bash
docker compose exec odoo odoo -d rubicon -u rubicon_uom --stop-after-init 2>&1 | tail -10
```

- [ ] **Step 3: Commit**

```bash
git add rubicon_addons/rubicon_uom/
git commit -m "feat(rubicon_uom): OWL service with convert/format/symbol/setUserPref"
```

---

## Task 7: OWL UOM selector component

**Files:**
- Create: `rubicon_addons/rubicon_uom/static/src/xml/rubicon_uom_selector.xml`
- Create: `rubicon_addons/rubicon_uom/static/src/js/rubicon_uom_selector.js`

- [ ] **Step 1: Create `static/src/xml/rubicon_uom_selector.xml`**

```xml
<?xml version="1.0" encoding="UTF-8"?>
<templates>
    <t t-name="rubicon_uom.UomSelector">
        <span class="d-inline-flex align-items-center gap-1">
            <select class="form-select form-select-sm py-0"
                    style="width: auto; font-size: 11px;"
                    t-on-change="onChangeUom">
                <t t-foreach="units" t-as="unit" t-key="unit.id">
                    <option t-att-value="unit.id"
                            t-att-selected="unit.id === activeUomId">
                        <t t-esc="unit.symbol"/>
                    </option>
                </t>
            </select>
            <button t-if="userHasPref"
                    t-on-click="onReset"
                    class="btn btn-sm btn-link p-0 text-muted"
                    title="Reset to default">↺</button>
        </span>
    </t>
</templates>
```

- [ ] **Step 2: Create `static/src/js/rubicon_uom_selector.js`**

```js
/** @odoo-module **/

import { Component } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { registry } from "@web/core/registry";

export class UomSelector extends Component {
    static template = "rubicon_uom.UomSelector";
    static props = {
        categoryCode: String,
        onUomChange: { type: Function, optional: true },
    };

    setup() {
        this.uomService = useService("rubicon_uom");
    }

    get units() {
        return this.uomService.getUnitsForCategory(this.props.categoryCode);
    }

    get activeUomId() {
        const uom = this.uomService.getActiveUom(this.props.categoryCode);
        return uom ? uom.id : null;
    }

    get userHasPref() {
        return this.uomService.hasUserPref(this.props.categoryCode);
    }

    async onChangeUom(ev) {
        const uomId = parseInt(ev.target.value, 10);
        await this.uomService.setUserPref(this.props.categoryCode, uomId);
        if (this.props.onUomChange) {
            this.props.onUomChange(this.props.categoryCode, uomId);
        }
    }

    async onReset() {
        await this.uomService.resetUserPref(this.props.categoryCode);
        if (this.props.onUomChange) {
            this.props.onUomChange(this.props.categoryCode, null);
        }
    }
}

registry.category("components").add("UomSelector", UomSelector);
```

- [ ] **Step 3: Deploy and commit**

```bash
docker compose exec odoo odoo -d rubicon -u rubicon_uom --stop-after-init 2>&1 | tail -10
git add rubicon_addons/rubicon_uom/
git commit -m "feat(rubicon_uom): UomSelector OWL component"
```

---

## Task 8: PDP workspace integration

**Files:**
- Modify: `rubicon_addons/pdp_frontend/__manifest__.py`
- Modify: `rubicon_addons/pdp_frontend/static/src/js/pdp_workspace.js`
- Modify: `rubicon_addons/pdp_frontend/static/src/xml/pdp_workspace.xml`
- Modify: `rubicon_addons/pdp_frontend/views/pdp_menus.xml`

- [ ] **Step 1: Add `rubicon_uom` dependency to `pdp_frontend/__manifest__.py`**

In the `depends` list, add `'rubicon_uom'`:
```python
'depends': [
    'web',
    'pdp_api',
    'pdp_picture',
    'rubicon_uom',
],
```

- [ ] **Step 2: Add UOM service + import to `pdp_workspace.js`**

At the top of the file, after existing imports:
```js
// In Odoo 18, module static files are aliased as @<module_name>/js/<file>
import { UomSelector } from "@rubicon_uom/js/rubicon_uom_selector";
```

Add `static components` to the `PdpWorkspace` class (right after the class declaration line `export class PdpWorkspace extends Component {`):
```js
export class PdpWorkspace extends Component {
    static template = "pdp_frontend.Workspace";
    static components = { UomSelector };
    // ... rest of class
```

> **Important:** OWL 2 requires sub-components to be declared in `static components` or the tag in the XML template will not render. Check if `PdpWorkspace` already has a `static template` line and add `static components` next to it.

In `setup()`, after `this.notification = useService("notification");`:
```js
this.uomService = useService("rubicon_uom");
```

In `onWillStart` (inside the async function, after existing awaits at the end):
```js
await this.uomService.load();
```

Add a method `onUomChange` to the class:
```js
onUomChange(categoryCode, uomId) {
    // Incrementing uomVersion causes OWL to re-render and re-evaluate
    // weightDisplay getters which read from the (now-updated) uomService.
    this.state.uomVersion = (this.state.uomVersion || 0) + 1;
}
```

Add `uomVersion: 0` to `this.state = useState({...})`.

Add a computed getter `weightDisplay`:
```js
get weightDisplay() {
    return {
        metalWeight: (value) => this.uomService.format(value, 'metal_weight', 3),
        stoneWeight: (value) => this.uomService.format(value, 'stone_weight', 3),
        metalSymbol: () => this.uomService.symbol('metal_weight'),
        stoneSymbol: () => this.uomService.symbol('stone_weight'),
    };
}
```

- [ ] **Step 3: Update `pdp_workspace.xml` — weight tab header with UOM selectors**

Find the weight tab panel opening tag (line ~224):
```xml
<div t-if="state.activeTab === 'weight' and state.selectedProductId" class="row g-3">
```

Add a UOM selector row just inside, before the existing content.
The hidden `t-esc="state.uomVersion"` is intentional — OWL's dependency tracker
reads it during render, so any increment of `uomVersion` triggers a re-render
and re-evaluates `weightDisplay`.

```xml
<div t-if="state.activeTab === 'weight' and state.selectedProductId" class="row g-3">
    <!-- Hidden read of uomVersion so OWL re-renders when UOM selection changes -->
    <t t-esc="state.uomVersion" t-out="''"/>
    <div class="col-12 d-flex gap-3 align-items-center pb-1 border-bottom mb-1">
        <small class="fw-bold text-muted">Display units:</small>
        <span class="d-flex align-items-center gap-1">
            <small class="text-muted">Metal:</small>
            <UomSelector categoryCode="'metal_weight'" onUomChange.bind="onUomChange"/>
        </span>
        <span class="d-flex align-items-center gap-1">
            <small class="text-muted">Stone:</small>
            <UomSelector categoryCode="'stone_weight'" onUomChange.bind="onUomChange"/>
        </span>
    </div>
    <!-- existing content below unchanged -->
```

Update the metal weight display cell (line ~271) to use converted value:
```xml
<!-- Before: -->
<td class="text-end"><t t-esc="(m.weight || 0).toFixed(3)"/></td>
<!-- After: -->
<td class="text-end"><t t-esc="weightDisplay.metalWeight(m.weight || 0)"/></td>
```

Update the column header for metal weight to show current unit symbol:
Find the `<th>` for the weight column in the metals section and add:
```xml
<th class="text-end">Weight (<t t-esc="weightDisplay.metalSymbol()"/>)</th>
```

- [ ] **Step 4: Add "Units of Measure" to PDP Settings menu in `pdp_menus.xml`**

After the existing `menu_pdp_settings_currency` item:
```xml
<menuitem id="menu_pdp_settings_uom"
          name="Units of Measure"
          parent="menu_pdp_frontend_settings"
          action="rubicon_uom.action_rubicon_uom_category"
          sequence="2"/>
```

- [ ] **Step 5: Deploy both modules**

```bash
docker compose exec odoo odoo -d rubicon -u rubicon_uom,pdp_frontend --stop-after-init 2>&1 | tail -20
```

- [ ] **Step 6: Smoke test in browser**

1. Open PDP workspace → Weight tab
2. Verify UOM selectors appear (Metal: `g ▾`, Stone: `ct ▾`)
3. Change Metal to `oz t` → metal weights update
4. Click ↺ → resets to `g`
5. Open PDP → Settings → Units of Measure → categories and units visible

- [ ] **Step 7: Commit**

```bash
git add rubicon_addons/rubicon_uom/ rubicon_addons/pdp_frontend/
git commit -m "feat(pdp_frontend): wire rubicon_uom service into weight tab with UOM selectors"
```

---

## Done

After all tasks pass:

- `rubicon_uom` module is installed with 4 categories and 8 pre-populated units
- Python conversion is tested (round-trip, cross-category guard, fallback chain)
- OWL service loads in one RPC and exposes convert/format/symbol/setUserPref/resetUserPref
- PDP weight tab shows converted values with per-dimension unit selectors
- Per-user preferences persist across sessions; reset restores global default
- "Units of Measure" is accessible from PDP Settings menu
