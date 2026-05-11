# SIS Analysis Module — Design Spec
**Date:** 2026-05-11
**Status:** Approved

## Context

The legacy `Analysis` desktop application (Windows/VCL) displays a pivot table of sales/order data: rows = customers, columns = years, values = amounts or quantities. It supports filters (Quarter, Month, Region, Country, Fair, Cost, Amount, Profit), grand totals, Sales/Orders toggle, and XLS export.

This spec describes the Odoo 18 equivalent as a new module `sis_analysis`, using Odoo's native pivot, graph, and search views to cover the same functionality with zero custom JavaScript.

## Architecture

**Module:** `sis_analysis`
**Dependencies:** `sis_document`, `sis_party`, `base`

```
sis_analysis/
├── __manifest__.py
├── __init__.py
├── models/
│   ├── __init__.py
│   └── sis_document_analysis.py
├── views/
│   ├── analysis_views.xml
│   └── menus.xml
└── security/
    └── ir.model.access.csv
```

No new data model is created. The module extends `sis.document` with two computed fields and adds views + menu entry.

## Data Model Extension

**File:** `models/sis_document_analysis.py`
**Inherits:** `sis.document`

| Field | Type | store | Purpose |
|---|---|---|---|
| `analysis_year` | Integer | True | Year extracted from `date_created`; stored for pivot performance |
| `analysis_country_group_ids` | M2M → `res.country.group` | False | Regions via `party_id.country_id.country_group_ids`; enables Region group-by |

`analysis_year` recomputes on module upgrade (no data migration needed).

Existing measures on `sis.document` used as-is: `total_amount`, `total_qty`, `total_cost`, `total_profit`.

## Views

### Pivot View (primary)
- **Row group:** `party_id` (customer)
- **Column group:** `analysis_year`
- **Default measure:** `total_amount`
- **Available measures:** `total_amount`, `total_qty`, `total_cost`, `total_profit`
- Native XLSX export button in the pivot toolbar

### Search View
Quick filters:
- **Sales** — `doc_type_id.category = 'S'`
- **Workshop** — `doc_type_id.category = 'W'`
- **This Year** — date filter on `date_created`
- **Last Year** — date filter on `date_created`

Group-by options:
- Region (`analysis_country_group_ids`)
- Country (`party_id.country_id`)
- Fair (`trade_fair_id`)
- Quarter (`date_created:quarter`)
- Month (`date_created:month`)

### Graph View
- Type: bar chart
- X axis: `analysis_year`
- Measure: `total_amount`
- Group: `party_id`

### List View
Standard list of `sis.document` columns: name, party_id, date_created, total_qty, total_amount, total_cost, total_profit. Used for drill-down from pivot.

## Menu

New entry under the existing `menu_sis_document_root`:

```xml
<menuitem name="Analysis" parent="menu_sis_document_root" sequence="50" action="action_sis_analysis"/>
```

## Security

Read-only access for all internal users (`base.group_user`). No dedicated group — same population as `sis_document`.

```csv
access_sis_analysis_user,sis.document.analysis.user,sis_document.model_sis_document,base.group_user,1,0,0,0
```

## Feature Mapping (legacy → Odoo)

| Legacy Feature | Odoo Equivalent |
|---|---|
| Company rows | Pivot row group: `party_id` |
| Year columns | Pivot col group: `analysis_year` |
| Sales toggle | Filter: `doc_type_id.category = 'S'` or measure `total_amount` |
| Orders toggle | Filter: `doc_type_id.category = 'W'` or measure `total_qty` |
| Quarter filter | Search group-by: `date_created:quarter` |
| Month filter | Search group-by: `date_created:month` |
| Region filter | Search group-by: `analysis_country_group_ids` (res.country.group) |
| Country filter | Search group-by: `party_id.country_id` |
| Fair filter | Search group-by: `trade_fair_id` |
| Cost / Amount / Profit | Pivot measures: `total_cost`, `total_amount`, `total_profit` |
| Grand Total | Native pivot grand total row/column |
| XLS Export | Native pivot XLSX export button |

## Out of Scope

- Custom OWL frontend
- QWeb PDF report replicating the matrix layout (can be added later)
- Write/edit access via the analysis view
