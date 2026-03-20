# Rubicon UOM — Design Spec
**Date:** 2026-03-20
**Status:** Approved

## Context

The PDP suite currently has no formal unit-of-measure system. A free-text field
`pdp_weight_uom_name` (in `pdp_price`) is the only UOM-related setting. Values
are stored as plain floats with no unit tracking, no conversion, and no
per-user preferences.

The goal is to introduce a reusable UOM module (`rubicon_uom`) usable across
all Rubicon software products, not just PDP.

---

## Architecture

### Module: `rubicon_uom`

- Depends on `base` only (no PDP dependency).
- Other modules add it as a dependency when needed (e.g. `pdp_frontend`, `pdp_price`).
- Follows the `rubicon_env` pattern: a general-purpose Rubicon infrastructure module.

### Models

#### `rubicon.uom.category`

Represents a measurable dimension.

| Field | Type | Notes |
|---|---|---|
| `name` | Char | Human label, e.g. "Metal Weight" |
| `code` | Char | Technical key, unique, e.g. `metal_weight` |
| `description` | Char | Optional |

`_rec_name = 'code'`

#### `rubicon.uom`

One unit within a category.

| Field | Type | Notes |
|---|---|---|
| `name` | Char | e.g. "Gramme" |
| `symbol` | Char | e.g. `g` |
| `category_id` | M2O → `rubicon.uom.category` | Required |
| `ratio` | Float (12,6) | Reference units in 1 of this unit. Reference unit = 1.0 |
| `is_reference` | Boolean | The unit stored in DB for this category |
| `is_global_default` | Boolean | Default display unit for this category |

`_rec_name = 'symbol'`

**Conversion formula:** `value_in_B = value_in_A * ratio_A / ratio_B`

**Constraints (ORM `@api.constrains`, not SQL partial indexes):**
- One `is_reference=True` unit per category
- One `is_global_default=True` unit per category

**Example verification:**
- 2 troy oz → g: `2 * 31.1035 / 1.0 = 62.207 g` ✓
- 10 ct → g: `10 * 1.0 / 5.0 = 2 g` (1 ct = 0.2 g) ✓
- 1 "relative to quartz" → g/cm³: `1.0 * 1.0 / 0.3774 ≈ 2.65 g/cm³` ✓

#### `rubicon.uom.user.pref`

Per-user display override.

| Field | Type | Notes |
|---|---|---|
| `user_id` | M2O → `res.users` | Required |
| `category_id` | M2O → `rubicon.uom.category` | Required |
| `uom_id` | M2O → `rubicon.uom` | Required; must belong to `category_id` (ORM constraint) |

**SQL constraint:** `unique(user_id, category_id)`

**ORM constraint:** `uom_id.category_id == category_id` — enforced via `@api.constrains('uom_id', 'category_id')`.

**Reset:** deleting the record reverts to global default.

---

## Pre-populated Data

Loaded via XML data files in the manifest (not a `post_init_hook`).

| Category code | Reference unit | ratio | Additional units | ratio |
|---|---|---|---|---|
| `metal_weight` | g | 1.0 | troy oz | 31.1035 |
| `stone_weight` | ct (carat) | 1.0 | g | 5.0 |
| `stone_density` | relative to quartz | 1.0 | g/cm³ | 0.3774 |
| `stone_size` | mm | 1.0 | inches | 25.4 |

Note on `stone_density` ratio: quartz density = 2.65 g/cm³, so ratio for g/cm³
= 1/2.65 ≈ 0.3774. Verification: `1.0 relative * 1.0 / 0.3774 ≈ 2.65 g/cm³` ✓

All reference units are also the global defaults at install.

---

## Backend Logic

### `rubicon.uom` — `convert()`

```python
def convert(self, value, to_uom):
    """Convert value expressed in self to to_uom.

    Raises UserError if self and to_uom belong to different categories.
    Returns 0 for None, False, or zero values.
    Negative values are allowed (e.g. adjustments).
    """
    if self.category_id != to_uom.category_id:
        raise UserError(...)
    if not value:
        return 0
    return value * self.ratio / to_uom.ratio
```

### `rubicon.uom.category` — `get_user_uom()`

```python
def get_user_uom(self, user_id=None):
    """Return the active display unit for a given user.

    Fallback chain: user pref → global default → reference unit.
    The reference unit is always present so this never returns False.
    """
```

### `rubicon.uom.category` — `set_global_default()`

```python
def set_global_default(self, uom_id):
    """Atomically set a new global default for this category.

    Unsets is_global_default on current default, sets it on uom_id.
    uom_id must belong to this category (validated).
    """
```

This method is the only entry point for changing the global default.
The settings UI calls it rather than writing `is_global_default` directly.

---

## Frontend (OWL)

### Service: `RubiconUomService` (tag: `rubicon_uom`)

Registered in the OWL service registry. Loaded once on workspace startup via `onWillStart`.

```js
await uomService.load()
// Single RPC: fetches all categories, units, and current user's prefs.
// Idempotent: calling load() again re-fetches (used after pref change).
// Before load() completes: format/convert return the raw value without symbol.
```

**Core assumption:** values are always stored in the reference unit.
`convert()` always converts from the reference unit to the user's preferred unit.

```js
uomService.format(value, 'metal_weight')   // → "2.52 oz t"  (reference → user pref)
uomService.convert(value, 'metal_weight')  // → 2.52 (float, reference → user pref)
uomService.symbol('metal_weight')          // → "oz t"

// For explicit source unit (e.g. value arriving in non-reference unit):
uomService.convertExplicit(value, fromUomId, toUomId)  // → float

uomService.setUserPref('metal_weight', uomId)  // saves to rubicon.uom.user.pref, then reloads
uomService.resetUserPref('metal_weight')        // deletes user pref record, then reloads
```

Workspaces inject the service via `useService('rubicon_uom')`.

### UOM Selector (per workspace toolbar)

A small dropdown per dimension showing the current symbol (e.g. `g ▾`).
Changing the selection calls `setUserPref`. A "↺ Reset" option calls `resetUserPref`.

---

## Settings UI

### Global defaults

- `res.config.settings` — new `<app>` block "Rubicon UOM" with a dropdown per category.
  Calls `set_global_default()` on save.
- Also accessible from PDP Settings menu → "Units of Measure".

### Per-user preferences

- Inline UOM selector in the workspace toolbar (one dropdown per visible dimension).
- Reset to global default via a "↺" button or "Reset" option in the dropdown.

---

## Error Handling & Fallbacks

| Situation | Behaviour |
|---|---|
| No user pref | Fall back to global default |
| No global default | Fall back to reference unit (always present) |
| Null / zero value | Return 0, skip conversion |
| Negative value | Allowed — converted normally |
| Cross-category conversion (Python) | Raise `UserError` |
| Unknown category code in OWL | Log warning, return raw value without unit symbol |
| Service not yet loaded (OWL) | Return raw value without unit symbol |

---

## Tests

**Python:**
- Round-trip conversion: `convert(convert(v, A→B), B→A) ≈ v` for all pre-populated pairs
- `convert()` raises `UserError` on cross-category call
- `get_user_uom` returns user pref when present
- `get_user_uom` returns global default when no user pref
- `get_user_uom` returns reference unit when no global default
- Deleting user pref reverts to global default
- `set_global_default()` atomically updates `is_global_default`
- `rubicon.uom.user.pref` ORM constraint rejects `uom_id` from wrong category

**OWL:** No unit tests planned (consistent with rest of project).

---

## Out of Scope

- Conversion of values already stored in DB (migration not included in v1).
- Non-linear conversions (e.g. °C ↔ °F). All conversions are ratio-based (linear).
- Currency handling — already managed by `pdp.currency.setting`.
