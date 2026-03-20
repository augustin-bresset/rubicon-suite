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

**Conversion formula:** `value_in_B = value_in_A * ratio_A / ratio_B`

**SQL constraints:**
- One reference unit per category
- One global default per category

#### `rubicon.uom.user.pref`

Per-user display override.

| Field | Type | Notes |
|---|---|---|
| `user_id` | M2O → `res.users` | Required |
| `category_id` | M2O → `rubicon.uom.category` | Required |
| `uom_id` | M2O → `rubicon.uom` | Required |

**SQL constraint:** unique(user_id, category_id)

**Reset:** deleting the record reverts to global default.

---

## Pre-populated Data

| Category code | Reference unit | Additional units |
|---|---|---|
| `metal_weight` | g (ratio 1.0) | troy oz (ratio 31.1035) |
| `stone_weight` | ct / carat (ratio 1.0) | g (ratio 5.0) |
| `stone_density` | relative to quartz (ratio 1.0) | g/cm³ (ratio 2.65) |
| `stone_size` | mm (ratio 1.0) | inches (ratio 25.4) |

All reference units are also the global defaults at install.

---

## Backend Logic

### `rubicon.uom`

```python
def convert(self, value, to_uom):
    """Convert value expressed in self to to_uom."""
    if not value:
        return 0
    return value * self.ratio / to_uom.ratio
```

### `rubicon.uom.category`

```python
def get_user_uom(self, user_id=None):
    """Return the active display unit for a given user.

    Fallback chain: user pref → global default → reference unit.
    """
```

---

## Frontend (OWL)

### Service: `RubiconUomService` (tag: `rubicon_uom`)

Registered in the OWL service registry. Loaded once on workspace startup.

```js
await uomService.load()
// Fetches all categories, units, and the current user's prefs from the backend.

uomService.format(value, 'metal_weight')   // → "2.52 oz t"
uomService.convert(value, 'metal_weight')  // → 2.52 (float)
uomService.symbol('metal_weight')          // → "oz t"

uomService.setUserPref('metal_weight', uomId)  // saves to rubicon.uom.user.pref
uomService.resetUserPref('metal_weight')        // deletes user pref record
```

Workspaces inject the service via `useService('rubicon_uom')`.

### UOM Selector (per workspace toolbar)

A small dropdown per dimension showing the current symbol (e.g. `g ▾`).
Changing the selection calls `setUserPref`. A "reset" option calls `resetUserPref`.

---

## Settings UI

### Global defaults

- `res.config.settings` — new `<app>` block "Rubicon UOM" with a dropdown per category.
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
| Unknown category code in OWL | Log warning, return raw value without unit symbol |

---

## Tests

**Python:**
- Round-trip conversion: `convert(convert(v, A→B), B→A) ≈ v`
- `get_user_uom` returns user pref when present
- `get_user_uom` returns global default when no user pref
- `get_user_uom` returns reference unit when no global default
- Deleting user pref reverts to global default

**OWL:** No unit tests planned (consistent with rest of project).

---

## Out of Scope

- Conversion of values already stored in DB (migration not included in v1).
- Support for non-linear conversions (e.g. °C ↔ °F). All conversions are linear (ratio only).
- Currency handling — already managed by `pdp.currency.setting`.
