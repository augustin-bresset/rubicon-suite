# SIS Document Footer Notes — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a configurable footer note per document type, editable by admins via a dedicated SIS Settings menu, rendered in the PDF report instead of the current hardcoded legal messages.

**Architecture:** Add a `footer_note` Text field to `sis.doc.type`. A new `doc_type_views.xml` exposes an editable tree view for admins. The PDF report reads `doc.doc_type_id.footer_note` directly. Initial data pre-populates SO and SI with the two existing legal messages.

**Tech Stack:** Odoo 18, Python models, XML views/data, QWeb PDF report templates.

---

## File Map

| File | Action | Responsibility |
|------|--------|---------------|
| `rubicon_addons/sis_document/models/doc_type.py` | Modify | Add `footer_note` field |
| `rubicon_addons/sis_document/data/doc_type_remarks.xml` | Create | Initial footer notes for SO and SI |
| `rubicon_addons/sis_document/__manifest__.py` | Modify | Register new view + data files |
| `rubicon_addons/sis_document/views/doc_type_views.xml` | Create | Editable tree view + window action |
| `rubicon_addons/sis_document/report/report_sis_document.xml` | Modify | Replace hardcoded remark block |
| `rubicon_addons/sis_frontend/views/sis_menus.xml` | Modify | Add Settings menu items |
| `rubicon_addons/sis_frontend/__manifest__.py` | Modify | Load `sis_settings_views.xml` |

---

## Task 1: Add `footer_note` field and initial data

**Files:**
- Modify: `rubicon_addons/sis_document/models/doc_type.py`
- Create: `rubicon_addons/sis_document/data/doc_type_remarks.xml`
- Modify: `rubicon_addons/sis_document/__manifest__.py`

- [ ] **Step 1: Add `footer_note` field to the model**

Replace the entire content of `rubicon_addons/sis_document/models/doc_type.py` with:

```python
from odoo import models, fields


class SisDocType(models.Model):
    _name = 'sis.doc.type'
    _description = 'SIS Document Type'
    _rec_name = 'name'

    code = fields.Char(required=True, index=True)
    name = fields.Char(required=True)
    category = fields.Selection([
        ('S', 'Sales'),
        ('W', 'Workshop/Production'),
    ], string='Category')
    footer_note = fields.Text(string='Footer Note')
```

- [ ] **Step 2: Create initial data file for SO and SI footer notes**

Create `rubicon_addons/sis_document/data/doc_type_remarks.xml`:

```xml
<?xml version="1.0" encoding="utf-8"?>
<odoo>
    <record id="sis_doctype_SO" model="sis.doc.type">
        <field name="footer_note">1. The diamonds herein invoiced have been purchased from legitimate sources not involved in funding conflict and in compliance with United Nation Resolutions and corresponding national laws. The seller hereby guarantees that these diamonds are conflict free and confirms adherence to the WDC SoW guidelines.

2. We certify that the non-industrial diamonds in our invoices were not mined, extracted, produced, or manufactured wholly or in part in Russian federal, notwithstanding any prior-stage processing in a third country.</field>
    </record>

    <record id="sis_doctype_SI" model="sis.doc.type">
        <field name="footer_note">1. The diamonds herein invoiced have been purchased from legitimate sources not involved in funding conflict and in compliance with United Nation Resolutions and corresponding national laws. The seller hereby guarantees that these diamonds are conflict free and confirms adherence to the WDC SoW guidelines.

2. We certify that the non-industrial diamonds in our invoices were not mined, extracted, produced, or manufactured wholly or in part in Russian federal, notwithstanding any prior-stage processing in a third country.</field>
    </record>
</odoo>
```

- [ ] **Step 3: Register `doc_type_remarks.xml` in `sis_document/__manifest__.py`**

In `rubicon_addons/sis_document/__manifest__.py`, add `'data/doc_type_remarks.xml'` after `'data/sis.doc.type.csv'`:

```python
'data': [
    'security/ir.model.access.csv',
    'data/sis.doc.type.csv',
    'data/doc_type_remarks.xml',
    'data/sis.doc.in.mode.csv',
    # sis.document and sis.document.item are business data — loaded via import_sis_odoo.py
    'report/report_action.xml',
    'report/report_sis_document.xml',
    'views/document_views.xml',
    'views/menus.xml',
],
```

- [ ] **Step 4: Commit**

```bash
git add rubicon_addons/sis_document/models/doc_type.py \
        rubicon_addons/sis_document/data/doc_type_remarks.xml \
        rubicon_addons/sis_document/__manifest__.py
git commit -m "feat(sis_document): add footer_note field to sis.doc.type with initial data"
```

---

## Task 2: Create the settings view for doc type remarks

**Files:**
- Create: `rubicon_addons/sis_document/views/doc_type_views.xml`
- Modify: `rubicon_addons/sis_document/__manifest__.py`

- [ ] **Step 1: Create the editable tree view and window action**

Create `rubicon_addons/sis_document/views/doc_type_views.xml`:

```xml
<?xml version="1.0" encoding="utf-8"?>
<odoo>
    <record id="view_sis_doc_type_remarks_tree" model="ir.ui.view">
        <field name="name">sis.doc.type.remarks.tree</field>
        <field name="model">sis.doc.type</field>
        <field name="arch" type="xml">
            <tree editable="bottom" string="Document Remarks">
                <field name="name" readonly="1"/>
                <field name="code" readonly="1"/>
                <field name="footer_note"/>
            </tree>
        </field>
    </record>

    <record id="action_sis_doc_type_remarks" model="ir.actions.act_window">
        <field name="name">Document Remarks</field>
        <field name="res_model">sis.doc.type</field>
        <field name="view_mode">tree</field>
        <field name="view_id" ref="view_sis_doc_type_remarks_tree"/>
    </record>
</odoo>
```

- [ ] **Step 2: Register `doc_type_views.xml` in `sis_document/__manifest__.py`**

Add `'views/doc_type_views.xml'` after `'views/document_views.xml'`:

```python
'data': [
    'security/ir.model.access.csv',
    'data/sis.doc.type.csv',
    'data/doc_type_remarks.xml',
    'data/sis.doc.in.mode.csv',
    # sis.document and sis.document.item are business data — loaded via import_sis_odoo.py
    'report/report_action.xml',
    'report/report_sis_document.xml',
    'views/document_views.xml',
    'views/doc_type_views.xml',
    'views/menus.xml',
],
```

- [ ] **Step 3: Commit**

```bash
git add rubicon_addons/sis_document/views/doc_type_views.xml \
        rubicon_addons/sis_document/__manifest__.py
git commit -m "feat(sis_document): add editable tree view for doc type footer notes"
```

---

## Task 3: Update PDF report to use `footer_note`

**Files:**
- Modify: `rubicon_addons/sis_document/report/report_sis_document.xml:437-457`

- [ ] **Step 1: Replace the hardcoded remark block**

In `rubicon_addons/sis_document/report/report_sis_document.xml`, replace lines 437–457 (the entire REMARK section):

Old block:
```xml
        <!-- ═══ REMARK ═══ -->
        <t t-set="rubicon" t-value="doc.env['res.partner'].sudo().search([('sis_code', '=', 'RUB')], limit=1)"/>
        <div class="sis-remark">
            <div class="sis-remark-title">Remark</div>
            <t t-if="rubicon and rubicon.sis_ship_stamp">
                <div style="white-space: pre-wrap;" t-field="rubicon.sis_ship_stamp"/>
            </t>
            <t t-else="">
                <p><b>1.</b> The diamonds herein invoiced have been purchased from legitimate
                sources not involved in
                funding conflict and in compliance with United Nation Resolutions and
                corresponding national laws.
                The seller hereby guarantees that these diamonds are conflict free and
                confirms adherence to the
                WDC SoW guidelines.</p>
                <p><b>2.</b> We certify that the non-industrial diamonds in our invoices were not
                mined, extracted, produced,
                or manufactured wholly or in part in Russian federal, notwithstanding
                any prior-stage processing in a third country.</p>
            </t>
        </div>
```

New block:
```xml
        <!-- ═══ REMARK ═══ -->
        <t t-if="doc.doc_type_id.footer_note">
            <div class="sis-remark">
                <div class="sis-remark-title">Remark</div>
                <div style="white-space: pre-wrap;" t-field="doc.doc_type_id.footer_note"/>
            </div>
        </t>
```

- [ ] **Step 2: Commit**

```bash
git add rubicon_addons/sis_document/report/report_sis_document.xml
git commit -m "feat(sis_document): render footer_note from doc type in PDF report"
```

---

## Task 4: Add Settings menu in SIS frontend

**Files:**
- Modify: `rubicon_addons/sis_frontend/views/sis_menus.xml`
- Modify: `rubicon_addons/sis_frontend/__manifest__.py`

- [ ] **Step 1: Add Settings menu items to `sis_menus.xml`**

In `rubicon_addons/sis_frontend/views/sis_menus.xml`, add the following block after the Tools menu section (after the `menu_sis_tools_product_browser` menuitem and before the Odoo Manager section):

```xml
    <!-- ========================================== -->
    <!-- 5. Settings Menu (admin only) -->
    <!-- ========================================== -->
    <menuitem id="menu_sis_settings"
              name="Settings"
              parent="menu_sis_root"
              sequence="40"
              groups="base.group_system"/>

    <menuitem id="menu_sis_settings_doc_remarks"
              name="Document Remarks"
              parent="menu_sis_settings"
              action="sis_document.action_sis_doc_type_remarks"
              sequence="10"
              groups="base.group_system"/>
```

- [ ] **Step 2: Add `sis_settings_views.xml` to `sis_frontend/__manifest__.py`**

Replace the `data` list in `rubicon_addons/sis_frontend/__manifest__.py`:

```python
'data': [
    'views/sis_menus.xml',
    'views/sis_settings_views.xml',
],
```

- [ ] **Step 3: Commit**

```bash
git add rubicon_addons/sis_frontend/views/sis_menus.xml \
        rubicon_addons/sis_frontend/__manifest__.py
git commit -m "feat(sis_frontend): add Settings > Document Remarks menu for admins"
```

---

## Task 5: Upgrade and smoke test

- [ ] **Step 1: Run the upgrade**

```bash
docker compose exec odoo odoo -d rubicon -u sis_document,sis_frontend --stop-after-init
```

Expected: upgrade completes with no errors. Watch for any XML/view loading errors in the log.

- [ ] **Step 2: Verify the Settings menu appears**

Log in as an Odoo admin. In the SIS app, confirm:
- A **Settings** item appears in the SIS root menu (sequence 40, between Tools and Odoo Manager)
- Under Settings, **Document Remarks** is present

- [ ] **Step 3: Verify the editable tree**

Open **SIS > Settings > Document Remarks**. Confirm:
- All 6 doc types are listed (CO, SE, SI, SO, SQ, SR)
- SO and SI have the two-paragraph legal text pre-filled in the Footer Note column
- CO, SE, SQ, SR have an empty Footer Note
- The Footer Note column is editable inline (click a cell → textarea appears)

- [ ] **Step 4: Verify the PDF report — SO with remark**

Open any Sales Order document. Click the print button to generate a PDF. Confirm:
- The **Remark** section appears at the bottom with the two legal paragraphs

- [ ] **Step 5: Verify the PDF report — SQ without remark**

Open any Sales Quotation document. Generate a PDF. Confirm:
- No **Remark** section appears (SQ has no footer note)

- [ ] **Step 6: Edit a footer note and verify it renders**

In **Document Remarks**, edit the SO footer note (e.g. add a line at the end). Save. Regenerate an SO PDF. Confirm the edited text appears in the Remark section.
