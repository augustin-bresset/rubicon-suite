# PDP Workspace Improvements + Metal Architecture Refactor

**Date:** 2026-03-20
**Scope:** Two phases — foundational DB/pricing refactor + workspace UX fixes, then Stones & Diamonds management menus.

---

## Context

The PDP (Product Design Process) module manages jewelry models and products with costing (metals, stones, labor, parts, misc). The current architecture stores metal weights at the **model level** (`pdp.product.model.metal`), shared by all products of a model. This causes a copy bug (metal weights can't be copied per-product), a fragile string coupling (`metal_version` char ↔ `product.metal` char), and prevents products that differ only in weight from being independently managed. The user selected **Option B**: move metals to product level.

---

## Phase 1 — Metal Architecture Refactor + Workspace Fixes

### 1. New Model: `pdp.product.metal`

**File:** `rubicon_addons/pdp_product/models/product_metal.py`

Fields:
- `product_id` — Many2one `pdp.product`, required, ondelete=cascade
- `metal_id` — Many2one `pdp.metal`
- `purity_id` — Many2one `pdp.metal.purity`
- `weight` — Float (g), digits=(6,3)
- `metal_version` — Char (optional label, e.g. "W", "W2"; kept for reference, not used in pricing)

Add `metal_ids = One2many('pdp.product.metal', 'product_id')` on `pdp.product`.

Remove `pdp.product.model.metal` model and all references once migration is complete.
Remove `metal_weights_ids` One2many from `pdp.product.model`.
Remove `get_metal_weights()` and `get_total_metal_weight()` methods from `pdp.product.model` (both iterate `metal_weights_ids`).

### 2. Data Migration Script

**File:** `ops/setup/migrate_metals_to_product.py`

For each `pdp.product.model.metal` record:
1. Find all products where `product.model_id = model_metal.model_id` AND `product.metal = model_metal.metal_version`
2. Create one `pdp.product.metal` record per matching product with the same `metal_id`, `purity_id`, `weight`, `metal_version`
3. Products with `product.metal` that matches no version get no metal record (data gap, acceptable)

Dry-run by default, `--apply` to execute. Print stats: matched, unmatched products.

### 3. Pricing Service Update

**Files:** `pdp_price/wizard/component_metal.py`, `component_metal_market.py`, `component_part.py`

Replace the model-level lookup:
```python
# OLD
model_metal = env['pdp.product.model.metal'].search([
    ('model_id', '=', product.model_id.id),
    ('metal_version', '=', product.metal),
], limit=1)
```
With product-level lookup iterating all metal records and summing costs:
```python
# NEW — replace the early-return guard too
if not product.metal_ids:
    return self._payload(...)  # no metal data, zero cost
for product_metal in product.metal_ids:
    # ... compute cost per metal record
```
Remove the old `if not product.model_id:` guard; replace with `if not product.metal_ids:`.

If a product has multiple metal records, sum costs across all of them (iterate `product.metal_ids`).

Also update `component_part.py` which uses `model_metal.purity_id` to find the margin — replace with `product_metal.purity_id` from the first `product.metal_ids` record. `component_part.py` currently falls back to searching purity by `code='18K'` when no purity is found; keep this existing fallback behaviour unchanged (do not replace with the null-purity pattern — the two components have different fallback requirements).

Update `pdp_price/tests/` accordingly.

### 4. Purity "ALL" Cleanup

**Current state:** Purity record `code='ALL'` (id=9) exists. 34 `pdp.margin.metal` records reference it. No `pdp.product.model.metal` (and therefore no future `pdp.product.metal`) records use it. These 34 margin records are effectively dead in pricing (exact purity match never hits them).

**Pre-requisite:** `pdp.margin.metal.metal_purity_id` is currently `required=True` in `pdp_margin/models/margin_metal.py`. Must change to `required=False` before the cleanup script can set it to False on those 34 rows. Add this model change to the module upgrade.

**Migration execution order (must follow this sequence):**
1. Run `ops/setup/migrate_metals_to_product.py` (while `pdp.product.model.metal` still exists)
2. Upgrade `pdp_margin` module (`odoo -u pdp_margin`) to apply `required=False` on `metal_purity_id`
3. Run `ops/setup/fix_purity_all.py` (sets 34 rows to null, deletes purity id=9)
4. Upgrade `pdp_product` module (`odoo -u pdp_product`) to drop `pdp.product.model.metal`

**Fix:**
- Change `metal_purity_id` to `required=False` in `pdp_margin/models/margin_metal.py`
- Migration script `ops/setup/fix_purity_all.py`:
  - Set `metal_purity_id = False` on the 34 `pdp.margin.metal` records (null = applies to all purities)
  - Delete purity record id=9 (`code='ALL'`)
- Update `component_metal.py` margin lookup to try exact purity first, then fall back to null. This applies inside the `product.metal_ids` loop — each metal record gets its own lookup:
  ```python
  for product_metal in product.metal_ids:
      purity_id = product_metal.purity_id.id if product_metal.purity_id else False
      margin_rec = Marge.search([('margin_id','=',margin.id), ('metal_purity_id','=',purity_id)], limit=1)
      if not margin_rec:
          margin_rec = Marge.search([('margin_id','=',margin.id), ('metal_purity_id','=',False)], limit=1)
      rate = margin_rec.rate if margin_rec else 1.0
      # ... compute cost for this metal record
  ```
- In the workspace purity filter dropdown: load purities with domain `[['code','!=','ALL']]` (becomes `[]` after deletion, but safe either way)

### 5. `copy_product_from_ui` — Add Metals Step

**File:** `pdp_product/models/product.py`

Add step 6 (after misc):
```python
if options.get('copy_metals'):
    for m in source.metal_ids:
        env['pdp.product.metal'].create({
            'product_id': new_product.id,
            'metal_id': m.metal_id.id,
            'purity_id': m.purity_id.id if m.purity_id else False,
            'weight': m.weight,
            'metal_version': m.metal_version,
        })
```

Also copy `source.metal` (char label) to new product.

Also update `get_weight_data()` (currently calls `self.model_id.get_metal_weights()`) — replace with a direct sum over `self.metal_ids` after migration.

**Pre-existing bug:** `confirmCopy()` in `pdp_workspace.js` builds the options dict without the `copy_metals` key despite `state.copyMetals` existing in state. Fix: add `copy_metals: this.state.copyMetals` to the options passed to the server call.

### 6. Workspace JS — Metals Become Product-Level

**File:** `pdp_frontend/static/src/js/pdp_workspace.js`

- Move `fetchProductMetals()` call from `selectModel()` to `selectProduct()`
- `fetchProductMetals()` searches `pdp.product.metal` with domain `[['product_id','=',productId]]`
- Fields: `['id','metal_id','purity_id','weight','metal_version']`
- Metal CRUD: `addMetal()`, `removeMetal()`, `setMetalField()` — save with `product_id`
- `saveAll()`: save metals with `product_id = selectedProductId`
- `confirmCopy()`: pass `copy_metals: this.state.copyMetals` in options
- Metal dropdown: show `opt.name` (not `opt.code`)
- Remove `metal_version` editable column (kept internally as label, not shown)

**`fetchWhereUsed()` disposal:** Remove the method and the Where Used tab entirely. The tab queried `pdp.product.model.metal` to show which products use a given metal; that use case is now covered by the product-level relationship directly. Removing it is the simpler path — it can be re-added later if needed via a direct query on `pdp.product.metal`.

### 7. Select Model "List" Button

Add `List` button next to the Model select in the top bar. Opens `showModelListModal`.

**Modal contents:**
- Title: "Select Model"
- Category filter dropdown at top — loads `pdp.product.category` records (`[['id','name']]`); filters the list
- Searchable text input (filters by model code)
- Table: Model | Drawing# | Quotation# — all columns searchable
- Row click → selects model + closes modal
- Cancel button

New state: `showModelListModal: false`, `modelListCategoryFilter: null`, `modelListSearch: ''`

### 8. Costing Summary — "Rate" Button

Add a `Rate` button (small, `btn-outline-secondary`) next to the Rate read-only input in the Costing tab pricing parameters section.

On click: `this.action.doAction('action_pdp_currency_setting')` — opens the currency settings list view.

### 9. Stones Tab — "Recut to" Bottom Bar

Track `selectedStoneKey: null` in state. Clicking a stone row sets `selectedStoneKey = sr._key` and highlights that row (`table-info` class).

Below the stones table, render a bottom bar when `selectedStoneKey` is set:
```
Recut to:  Shape [dropdown]  |  Size [dropdown]  |  Weight [input]
```
These inputs bind to `reshaped_shape_id`, `reshaped_size_id`, `reshaped_weight` on the selected row via `setStoneField()`. Changing any value marks `_dirty`. The inline table columns for Rec. Shape / Rec. Size / Rec. Wgt remain as read-only display columns.

### 10. Purity Filter — Remove Duplicate "All"

Load purities with ORM domain `[['code','!=','ALL']]` (both before and after the cleanup script). The hardcoded `<option value="">All</option>` in the select is the only "show all" option.

Same fix applies to the Costing tab purity filter and the Metals tab purity filter.

### 11. Labor Tab — "Part" Button

Add a `Part` button in the top-right of the Labor etc. tab header area. On click:
```javascript
this.action.doAction({
    type: 'ir.actions.act_window',
    name: 'Parts',
    res_model: 'pdp.part',
    view_mode: 'list,form',
})
```

### 12b. Weight Tab — Fix Stone Display

**File:** `pdp_frontend/static/src/js/pdp_workspace.js` + `pdp_workspace.xml`

**Issue 1 — Weight often 0:** `pdp.product.stone.weight` is a stored computed field that sources from `stone_id.weight` (itself a related to `pdp.stone.weight`). When the weight table has no matching record the stored value is 0 and stays 0. The JS `fetchProductStones()` doesn't include `weight` in the stone-details read from `pdp.stone`, so there is no fallback.

**Fix:** Add `"weight"` to the `orm.read("pdp.stone", ...)` call in `fetchProductStones()`. Build `stoneOriginal[].weight` as `s.weight || detail.weight || 0`.

**Issue 2 — Shows stone code instead of descriptive columns:** `stoneOriginal` and `stoneRecut` are built with a `stone` field that holds `stone_id[1]` (the ORM display name, which is the code). The `to_dict_original()` method on the model already produces the correct shape with `type`, `shade`, `shape`, `pieces`, `weight`.

**Fix:** Rebuild both arrays using `detailMap` (already populated at that point):
- `stoneOriginal`: `{ type, shade, shape, pieces, weight }` — type from `detail.type_id[1]`, shade from `detail.shade_id[1]`, shape from `detail.shape_id[1]`, weight from `s.weight || detail.weight || 0`
- `stoneRecut`: same columns, shape overridden by `s.reshaped_shape_id[1]` if set, weight from `s.reshaped_weight || s.weight || detail.weight || 0`

Update the Weight tab XML: replace "Stone/Pcs/Wt" columns with "Type/Shade/Shape/Pcs/Wt" for both sub-tables. Adjust `colspan` on the empty-row fallback accordingly.

### 12. Matching Tab — Fix Picture Loading

`fetchMatchingModels()` currently uses `search_read` with `picture_id` field. Since `picture_id` is a non-stored computed Many2one, switch to `orm.read()` for the matched IDs to ensure the compute is triggered:

```javascript
const models = await this.orm.read('pdp.product.model', matchedIds, ['id', 'code', 'picture_id']);
```

Display image in matching table: `/web/image/pdp.picture/{picture_id[0]}/image_1920`. If `picture_id` is false, show nothing (no image uploaded for that model — expected).

---

## Phase 2 — Stones & Diamonds Submenus

### 13. Menu Restructure

In `pdp_frontend/views/pdp_menus.xml`:
- Remove `action=` attribute from `menu_pdp_manage_stones` (becomes parent menu only)
- Add three child menu items: **Types & Shapes**, **Unit Cost**, **Unit Weight**
- Each points to a new `ir.actions.client` with an OWL component tag

### 14. Types & Shapes Window (`StoneReferentialWorkspace`)

New OWL client action. One window with 5 tabs: **Categories | Types | Shapes | Shades | Sizes**.

Each tab shows an inline-editable table:
- Categories: `code`, `name`
- Types: `code`, `name`, `category_id` (dropdown), `density`
- Shapes: `code`, `shape` (the actual field name on `pdp.stone.shape`)
- Shades: `code`, `shade` (the actual field name on `pdp.stone.shade`)
- Sizes: `code`, `name` — `pdp.stone.size` currently only has `name`; add `code = fields.Char()` to the model as part of this work

Full CRUD per tab: Add row, delete row (with deleted-ID tracking), Save button. No cross-tab dependencies (each tab saves independently to its model).

Models: `pdp.stone.category`, `pdp.stone.type`, `pdp.stone.shape`, `pdp.stone.shade`, `pdp.stone.size`

### 15. Unit Cost Window (`StoneCostWorkspace`)

New OWL client action.

**Header filters (cascading):**
- Type dropdown → Shape dropdown → Shade dropdown
- Changing Type clears Shape and Shade selections and reloads the table
- Changing Shape clears Shade and reloads

**Table:** Fetches `pdp.stone` records matching the selected type+shape+shade. Columns: Size | Unit Cost (editable float) | Currency (editable dropdown). Each row is a `pdp.stone` record.

**Pieces input:** Integer input (used for print only, not saved to DB).

**Save button:** Writes `cost` and `currency_id` changes back to `pdp.stone` records (dirty rows only).

**Print button:** Calls a server-side route/RPC to generate the Stone Cost Chart PDF report, opens in new tab.

### 16. Unit Weight Window (`StoneWeightWorkspace`)

Same structure as Unit Cost. Manages `pdp.stone.weight` records.

**Table:** Load all `pdp.stone.size` records. For each size, look up the matching `pdp.stone.weight` record with `[type_id=X, shape_id=Y, shade_id=Z, size_id=size.id]`. If one exists, pre-populate its weight; if not, the row shows an empty weight. The table always shows all sizes — there is no size-level filter. Saving creates a new `pdp.stone.weight` record for rows with a weight value and no existing record; writes the `weight` field on rows with an existing record.

Note: `pdp.stone.size` has no FK to type/shape — sizes are universal. The `pdp.stone.weight` table uniquely constrains `(type_id, shape_id, shade_id, size_id)`.

Save writes weight changes. No print required.

### 17. Stone Cost Chart PDF (QWeb Report)

**File:** `pdp_stone/report/report_stone_cost_chart.xml` + `report_action.xml`

Header: Stone Type (name), Stone Category (name), Shade (name), date
Table: Size | Unit Cost | Currency
Footer: generated by PDP

Triggered from Unit Cost window via `this.action.doAction`:
```javascript
this.action.doAction({
    type: 'ir.actions.report',
    report_type: 'qweb-pdf',
    report_name: 'pdp_stone.report_stone_cost_chart',
    data: { type_id: X, shape_id: Y, shade_id: Z },
});
```

---

## Files Changed — Summary

### New files
- `pdp_product/models/product_metal.py`
- `ops/setup/migrate_metals_to_product.py`
- `ops/setup/fix_purity_all.py`
- `pdp_frontend/static/src/js/stone_referential_workspace.js`
- `pdp_frontend/static/src/xml/stone_referential_workspace.xml`
- `pdp_frontend/static/src/js/stone_cost_workspace.js`
- `pdp_frontend/static/src/xml/stone_cost_workspace.xml`
- `pdp_frontend/static/src/js/stone_weight_workspace.js`
- `pdp_frontend/static/src/xml/stone_weight_workspace.xml`
- `pdp_stone/report/report_stone_cost_chart.xml`
- `pdp_stone/report/report_action.xml`

### Modified files
- `pdp_product/models/product.py` — add copy_metals, remove model metal helpers
- `pdp_product/models/model.py` — remove `metal_weights_ids` One2many
- `pdp_product/models/__init__.py` — add product_metal, remove model_metal
- `pdp_product/__manifest__.py` — update data/security
- `pdp_price/wizard/component_metal.py` — product-level lookup + purity fallback
- `pdp_price/wizard/component_metal_market.py` — product-level lookup
- `pdp_price/wizard/component_part.py` — product-level purity lookup
- `pdp_price/tests/test_component_metal.py` — update fixtures
- `pdp_price/tests/test_component_part.py` — structural rewrite: fixtures must create `pdp.product.metal` records instead of `pdp.product.model.metal`; test assertions around purity lookup change to cover null-fallback path
- `pdp_frontend/static/src/js/pdp_workspace.js` — all workspace fixes
- `pdp_frontend/static/src/xml/pdp_workspace.xml` — all workspace fixes
- `pdp_frontend/views/pdp_menus.xml` — restructure Stones & Diamonds menu
- `pdp_frontend/models/pdp_frontend_service.py` — lines 93-94 reference `product.model_id.metal_weights_ids`; replace with `product.metal_ids`
- `pdp_frontend/views/pdp_frontend_templates.xml` — lines 411, 497 loop over `product.model_id.metal_weights_ids`; line 499 uses `m.metal_version`; replace all with `product.metal_ids` / `m.metal_version`
- `pdp_margin/models/margin_metal.py` — change `metal_purity_id` from `required=True` to `required=False`
- `pdp_product/views/pdp_views.xml` — remove `view_pdp_product_model_metal_list` view record (lines 46-59 reference `pdp.product.model.metal`)
- `pdp_product/views/pdp_menus.xml` — remove `action_pdp_product_model_metal` action record and `menu_pdp_product_model_metal` menu item (lines 43-53)
- `pdp_product/security/ir.model.access.csv` — remove `pdp.product.model.metal` access row; add `pdp.product.metal` access row
- `rubicon_import/raw_to_data/raw_to_data_product.py` — update lines 387-409 which hardcode `model_name="pdp.product.model.metal"` and `metal_version`; change to target `pdp.product.metal` with `product_id` key (or mark as defunct if import will not be re-run)
- `pdp_api/models/pdp_api_service.py` — line 81 calls `product.model_id.get_total_metal_weight()` which will be removed; replace with `sum(m.weight for m in product.metal_ids)`
- `pdp_product/tests/test_domain_methods.py` — tests `get_metal_weights()` which will be deleted; remove or rewrite tests
- `pdp_product/tests/test_domain_xmlrpc.py` — tests `get_metal_weights()` which will be deleted; remove or rewrite tests
- `pdp_stone/__manifest__.py` — add report; register `pdp_stone/models/stone_size.py` change
- `pdp_stone/models/stone_size.py` — add `code = fields.Char()` field
- `ops/audit/audit_model.py` — remove `'pdp.product.model.metal'` from hardcoded model list; add `'pdp.product.metal'`
- `ops/audit/audit_counts.py` — same substitution
- `ops/import/import_csv.py` — line 40 imports into `pdp.product.model.metal`; update to `pdp.product.metal` with `product_id` key

### Deleted files
- `pdp_product/models/model_metal.py` (after migration)

---

## Constraints & Notes

- Migration must run before module upgrade (model_metal still exists during migration)
- `metal_version` char on `pdp.product` is kept as a display label; no pricing logic uses it after refactor
- Products with no matching metal version get no metal record — this is a data gap from the original import, not a code error
- The `pdp.product.model` still loads its category and metadata; only the metal One2many is removed
- Phase 2 components (StoneReferential, StoneCost, StoneWeight) are independent of Phase 1 and can be implemented in parallel
