# SIS Document Footer Notes — Design Spec
**Date:** 2026-04-25

## Problem

Legal compliance messages (Kimberley Process / conflict diamonds, Russian diamond certification) are currently hardcoded in the PDF report template `sis_document/report/report_sis_document.xml`. They cannot be edited without touching code. The requirement is a dedicated settings menu where administrators can configure a footer note per document type.

## Goals

- Administrators can edit the footer note for each document type via a dedicated Settings menu in SIS.
- The PDF report reads the footer note from the document type and renders it at the bottom of the document.
- If no footer note is set for a document type, the Remark section is omitted entirely.
- Access is restricted to Odoo administrators (`base.group_system`).

## Out of Scope

- Per-document override of the footer note.
- Per-user or per-language notes.
- Toggling individual remark paragraphs independently.

---

## Architecture

### 1. Model: `sis.doc.type` — new field

**File:** `sis_document/models/doc_type.py`

Add one field:
```python
footer_note = fields.Text(string='Footer Note')
```

No other changes to the model.

### 2. Settings View — editable tree on `sis.doc.type`

**File:** `sis_document/views/doc_type_views.xml` (new file — `document_views.xml` is reserved for `sis.document`)

New tree view with `editable="bottom"`:
- Columns: **Name**, **Code**, **Footer Note**

New `ir.actions.act_window`:
- Model: `sis.doc.type`
- View mode: `tree` (editable)
- Name: `Document Remarks`

### 3. Menu

**File:** `sis_frontend/views/sis_menus.xml`

```xml
<menuitem id="menu_sis_settings" name="Settings"
          parent="menu_sis_root" sequence="40"
          groups="base.group_system"/>

<menuitem id="menu_sis_settings_doc_remarks" name="Document Remarks"
          parent="menu_sis_settings"
          action="sis_document.action_sis_doc_type_remarks"
          sequence="10"
          groups="base.group_system"/>
```

### 4. PDF Report

**File:** `sis_document/report/report_sis_document.xml`

Replace the current hardcoded remark block (lines 438–457) with:

```xml
<t t-if="doc.doc_type_id.footer_note">
    <div class="sis-remark">
        <div class="sis-remark-title">Remark</div>
        <div style="white-space: pre-wrap;" t-field="doc.doc_type_id.footer_note"/>
    </div>
</t>
```

The old `sis_ship_stamp` fallback logic is removed entirely.

### 5. Initial Data

**File:** `sis_document/data/sis.doc.type.csv` (update existing records)

Pre-populate `footer_note` on the **SO** (Sales Order) and **SI** (Invoice) doc types with the two current legal messages:

```
1. The diamonds herein invoiced have been purchased from legitimate sources not involved in
funding conflict and in compliance with United Nation Resolutions and corresponding national laws.
The seller hereby guarantees that these diamonds are conflict free and confirms adherence to the
WDC SoW guidelines.

2. We certify that the non-industrial diamonds in our invoices were not mined, extracted, produced,
or manufactured wholly or in part in Russian federal, notwithstanding any prior-stage processing
in a third country.
```

Other doc types (SQ, CO, SE, SR) get no initial footer note.

### 6. Manifest Fix

**File:** `sis_frontend/__manifest__.py`

Add `'views/sis_settings_views.xml'` to the `data` list. This file exists but is currently not loaded.

---

## Security

No new security group is introduced. The menu and action are gated on `base.group_system` (Odoo admin), consistent with the "admin only" requirement.

The `ir.model.access.csv` for `sis_document` already grants read/write on `sis.doc.type` to internal users; no changes needed there since the menu itself restricts access.

---

## Files Changed

| File | Change |
|------|--------|
| `sis_document/models/doc_type.py` | Add `footer_note` field |
| `sis_document/views/doc_type_views.xml` | New file: editable tree view + action for `sis.doc.type` |
| `sis_document/data/sis.doc.type.csv` | Pre-populate footer notes for SO and SI |
| `sis_document/report/report_sis_document.xml` | Replace hardcoded remark block |
| `sis_frontend/views/sis_menus.xml` | Add Settings menu + Document Remarks submenu |
| `sis_frontend/__manifest__.py` | Add `sis_settings_views.xml` to data list |

---

## Upgrade Command

```bash
docker compose exec odoo odoo -d rubicon -u sis_document,sis_frontend --stop-after-init
```
