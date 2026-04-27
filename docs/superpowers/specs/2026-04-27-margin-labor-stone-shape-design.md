# Margin Labor Simplification + Stone Shape — Design Spec
**Date:** 2026-04-27

## Problem

The current `pdp.margin.labor` table has 6 rows per margin (one per labor type: CAS, FIL, ASS, POL, REC, SET), but all 6 rows always carry the same rate. This is redundant. The business actually distinguishes two labor categories: metal labor and stone labor. The source data (`Margins.csv`) already has separate columns for these two rates (col[5] and col[7]), which happen to be equal today but the employer wants the separation maintained.

Additionally, `pdp.margin.stone` has three stone dimensions (type, size, shade) but is missing `shape`, which exists in the source data (`StoneMargins.csv` col[3]) but was never imported.

## Goals

- Replace `pdp.margin.labor` (6-row table) with two Float fields directly on `pdp.margin`.
- Metal labor (CAS, FIL, ASS, POL) uses `labor_metal_rate`.
- Stone labor (REC, SET) uses `labor_stone_rate`.
- Add `stone_shape_id` to `pdp.margin.stone` as a fourth optional dimension.
- All four stone dimensions (type, shape, size, shade) act as wildcards when None; the most specific match wins at price computation time.
- Keep `pdp.margin.stone.conditional` unchanged.

## Out of Scope

- Changes to `pdp.margin.addon`, `pdp.margin.part`, `pdp.margin.metal`.
- Changing the values of existing margins.

---

## Architecture

### 1. `pdp.margin` model — new fields

**File:** `pdp_margin/models/margin.py`

Add:
```python
labor_metal_rate = fields.Float(string='Metal Labor Rate', digits=(5, 3))
labor_stone_rate = fields.Float(string='Stone Labor Rate', digits=(5, 3))
```

Source: `Margins.csv` col[5] → `labor_metal_rate`, col[7] → `labor_stone_rate`.

### 2. `pdp.margin.labor` — removed

- Delete `pdp_margin/models/margin_labor.py`
- Remove from `pdp_margin/models/__init__.py`
- Remove `pdp_margin/data/pdp.margin.labor.csv` from manifest
- Remove any views referencing `pdp.margin.labor`
- Remove security entry for `pdp.margin.labor`

### 3. `pdp.margin.stone` — add `stone_shape_id`

**File:** `pdp_margin/models/margin_stone.py`

Add:
```python
stone_shape_id = fields.Many2one(
    'pdp.stone.shape', string='Shape', index=True
)
```

All four dimensions (`stone_type_id`, `stone_shape_id`, `stone_size_id`, `stone_shade_id`) remain optional. None = wildcard.

Source: `StoneMargins.csv` col[3]. Values "1" or "All" → treated as None (wildcard).

### 4. Price computation — `pdp_price`

**`component_labor.py`**: Replace lookup in `pdp.margin.labor` with direct field read:
- labor_type ∈ {CAS, FIL, ASS, POL} → `margin.labor_metal_rate`
- labor_type ∈ {REC, SET} → `margin.labor_stone_rate`

**`component_stone.py`**: Add `stone_shape_id` to the stone margin lookup. Use a fallback chain from most specific to least specific:
1. type + shape + size + shade
2. type + shape + size
3. type + shape + shade
4. type + shape
5. type + size + shade
6. type + size
7. type + shade
8. type only
9. all None (global fallback)

First match wins.

### 5. Import (`raw_to_data_margin.py`)

**`pdp.margin` section:**
- Add `labor_metal_rate` and `labor_stone_rate` to `fieldnames`
- In `row_to_dict`: `labor_metal_rate = safe_float(row[5])`, `labor_stone_rate = safe_float(row[7])`

**`pdp.margin.labor` section:** Remove entirely.

**`pdp.margin.stone` section:**
- Add `stone_shape_id` to `fieldnames`
- In `row_to_dict`: extract `col[3]`, strip whitespace; if value is "1", "All", or empty → output `''` (None); otherwise output the shape code.
- Update `id` to include shape in key to avoid collisions.

### 6. Generated data files

| File | Change |
|------|--------|
| `pdp_margin/data/pdp.margin.csv` | +2 columns: `labor_metal_rate`, `labor_stone_rate` |
| `pdp_margin/data/pdp.margin.stone.csv` | +1 column: `stone_shape_id` |
| `pdp_margin/data/pdp.margin.labor.csv` | Removed from manifest and deleted |

### 7. Manifest

**`pdp_margin/__manifest__.py`:** Remove `data/pdp.margin.labor.csv` from data list.

---

## Labor Type → Category Mapping

| Labor Type | Code | Category |
|---|---|---|
| Casting | CAS | metal |
| Filing | FIL | metal |
| Assembling | ASS | metal |
| Polishing | POL | metal |
| Recutting | REC | stone |
| Setting | SET | stone |

---

## Upgrade Command

```bash
docker compose exec odoo odoo -d rubicon -u pdp_margin,pdp_price,pdp_frontend --stop-after-init
```

Note: the `pdp.margin.labor` table will be left in the database as an orphan table after the module upgrade (Odoo does not drop tables on module uninstall). This is safe — the model is no longer referenced.

Note: changing the ID format for stone margin records (adding shape to the key) means existing records cannot be matched on re-import. The implementation plan must truncate `pdp.margin.stone` before re-importing to avoid duplicates.
