# rubicon_frontend Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Créer le module `rubicon_frontend` qui centralise les design tokens et le thème Odoo global, puis migrer `sis_document` et adapter `pdp_frontend`/`sis_frontend` pour consommer ces tokens.

**Architecture:** Module technique Odoo sans menus ni vues, uniquement des assets SCSS chargés dans `web._assets_primary_variables` et `web.assets_backend`. Les modules existants déclarent `rubicon_frontend` comme dépendance ; leurs SCSS locaux sont supprimés ou remplacés par des classes `.rbn-*`.

**Tech Stack:** Odoo 18, SCSS, CSS custom properties, Bootstrap 5 (via Odoo)

---

## File Map

| Action | Fichier |
|--------|---------|
| Créer | `rubicon_addons/rubicon_frontend/__init__.py` |
| Créer | `rubicon_addons/rubicon_frontend/__manifest__.py` |
| Créer | `rubicon_addons/rubicon_frontend/static/src/scss/variables.scss` |
| Créer | `rubicon_addons/rubicon_frontend/static/src/scss/odoo_overrides.scss` |
| Créer | `rubicon_addons/rubicon_frontend/static/src/scss/workspace.scss` |
| Modifier | `rubicon_addons/sis_document/__manifest__.py` |
| Supprimer | `rubicon_addons/sis_document/static/src/scss/variables.scss` |
| Supprimer | `rubicon_addons/sis_document/static/src/scss/style.scss` |
| Modifier | `rubicon_addons/pdp_frontend/__manifest__.py` |
| Modifier | `rubicon_addons/pdp_frontend/static/src/xml/pdp_workspace.xml` |
| Modifier | `rubicon_addons/sis_frontend/static/src/xml/sis_workspace.xml` |

---

## Task 1 : Créer le module rubicon_frontend

**Files:**
- Create: `rubicon_addons/rubicon_frontend/__init__.py`
- Create: `rubicon_addons/rubicon_frontend/__manifest__.py`

- [ ] **Step 1 : Créer `__init__.py` (vide)**

```python
```

Fichier : `rubicon_addons/rubicon_frontend/__init__.py` — vide, requis par Odoo.

- [ ] **Step 2 : Créer `__manifest__.py`**

```python
{
    'name': 'Rubicon Frontend',
    'version': '18.0.1.0.0',
    'license': 'LGPL-3',
    'category': 'Technical',
    'summary': 'Shared SCSS design tokens and theme for Rubicon suite',
    'depends': ['web'],
    'assets': {
        'web._assets_primary_variables': [
            ('prepend', 'rubicon_frontend/static/src/scss/variables.scss'),
        ],
        'web.assets_backend': [
            'rubicon_frontend/static/src/scss/odoo_overrides.scss',
            'rubicon_frontend/static/src/scss/workspace.scss',
        ],
    },
    'installable': True,
    'application': False,
    'auto_install': False,
}
```

- [ ] **Step 3 : Commit**

```bash
git add rubicon_addons/rubicon_frontend/
git commit -m "feat(rubicon_frontend): scaffold module with manifest"
```

---

## Task 2 : Créer `variables.scss` (design tokens)

**Files:**
- Create: `rubicon_addons/rubicon_frontend/static/src/scss/variables.scss`

- [ ] **Step 1 : Créer le fichier**

```scss
// Variables SCSS Odoo (compilées au build)
$o-brand-primary: #000000;
$o-brand-odoo: #000000;
$o-navbar-background-color: #000000;
$o-navbar-color: #ffffff;
$primary: $o-brand-primary;
$secondary: #6c757d;
$success: #28a745;
$info: #17a2b8;
$warning: #ffc107;
$danger: #dc3545;
$black: #000 !default;
$white: #fff !default;

// CSS custom properties Rubicon (disponibles à runtime dans les templates)
:root {
    --rbn-brand: #000000;
    --rbn-ws-bg: #f2f2f2;
    --rbn-toolbar-bg: #ffffff;
    --rbn-border: #cccccc;
    --rbn-border-light: #dddddd;
    --rbn-font-ws: 13px;
    --rbn-font-table: 12px;
}
```

- [ ] **Step 2 : Commit**

```bash
git add rubicon_addons/rubicon_frontend/static/src/scss/variables.scss
git commit -m "feat(rubicon_frontend): add design tokens in variables.scss"
```

---

## Task 3 : Créer `odoo_overrides.scss` (thème global Odoo)

**Files:**
- Create: `rubicon_addons/rubicon_frontend/static/src/scss/odoo_overrides.scss`

C'est le contenu exact de `sis_document/static/src/scss/style.scss` déplacé ici.

- [ ] **Step 1 : Créer le fichier**

```scss
// Odoo 18 Black and White Theme Overrides

:root {
    --o-brand-primary: #000000 !important;
    --o-brand-odoo: #000000 !important;
    --o-navbar-background-color: #000000 !important;
    --o-navbar-color: #ffffff !important;
    --o-navbar-entry-focus-background-color: #333333 !important;
    --o-btn-primary-bg: #000000 !important;
    --o-btn-primary-border: #000000 !important;
    --o-btn-primary-color: #ffffff !important;
    --o-app-drawer-background: #000000 !important;
}

body {
    background-color: #ffffff !important;
}

.o_main_navbar {
    background-color: #000000 !important;
    border-bottom: 1px solid #333 !important;

    .o_menu_brand,
    .o_nav_entry,
    .o_menu_sections .nav-link {
        color: #ffffff !important;

        &:hover {
            background-color: #333333 !important;
        }
    }
}

.btn-primary {
    background-color: #000000 !important;
    border-color: #000000 !important;
    color: #ffffff !important;
    --hover-background: #333333;
    --hover-border: #333333;

    &:hover,
    &:focus,
    &:active {
        background-color: #333333 !important;
        border-color: #333333 !important;
    }
}

.progress-bar {
    background-color: #000000 !important;
}

.o_list_table {
    thead {
        background-color: #f8f9fa !important;
        color: #000000 !important;

        th {
            color: #000000 !important;
            border-bottom: 2px solid #000 !important;
        }
    }
}

::selection {
    background: #000000 !important;
    color: #ffffff !important;
}

.dropdown-item.active,
.dropdown-item:active {
    background-color: #000000 !important;
    color: #ffffff !important;
}

.o_notebook .nav-link.active {
    border-top-color: #000000 !important;
    color: #000000 !important;
}
```

- [ ] **Step 2 : Commit**

```bash
git add rubicon_addons/rubicon_frontend/static/src/scss/odoo_overrides.scss
git commit -m "feat(rubicon_frontend): add odoo_overrides.scss (moved from sis_document)"
```

---

## Task 4 : Créer `workspace.scss` (classes utilitaires)

**Files:**
- Create: `rubicon_addons/rubicon_frontend/static/src/scss/workspace.scss`

- [ ] **Step 1 : Créer le fichier**

```scss
.rbn-workspace {
    font-size: var(--rbn-font-ws);
    background: var(--rbn-ws-bg);
}

.rbn-toolbar {
    background: var(--rbn-toolbar-bg);
    border-bottom: 1px solid var(--rbn-border);
}

.rbn-table {
    font-size: var(--rbn-font-table);
}
```

- [ ] **Step 2 : Commit**

```bash
git add rubicon_addons/rubicon_frontend/static/src/scss/workspace.scss
git commit -m "feat(rubicon_frontend): add workspace utility classes"
```

---

## Task 5 : Migrer sis_document

**Files:**
- Modify: `rubicon_addons/sis_document/__manifest__.py`
- Delete: `rubicon_addons/sis_document/static/src/scss/variables.scss`
- Delete: `rubicon_addons/sis_document/static/src/scss/style.scss`

- [ ] **Step 1 : Mettre à jour `__manifest__.py`**

Remplacer :
```python
'depends': ['base', 'sis_party', 'pdp_product'],
...
'assets': {
    'web._assets_primary_variables': [
        ('prepend', 'sis_document/static/src/scss/variables.scss'),
    ],
    'web.assets_backend': [
        'sis_document/static/src/scss/style.scss',
    ],
},
```

Par :
```python
'depends': ['base', 'sis_party', 'pdp_product', 'rubicon_frontend'],
...
# Supprimer entièrement le bloc 'assets'
```

Le fichier final ne doit plus avoir de clé `'assets'`.

- [ ] **Step 2 : Supprimer les fichiers SCSS**

```bash
git rm rubicon_addons/sis_document/static/src/scss/variables.scss
git rm rubicon_addons/sis_document/static/src/scss/style.scss
```

Si le dossier `scss/` devient vide, supprimer également :
```bash
rmdir rubicon_addons/sis_document/static/src/scss/
```

- [ ] **Step 3 : Vérifier l'upgrade**

```bash
docker compose exec odoo odoo -d rubicon -u rubicon_frontend,sis_document --stop-after-init
```

Expected : aucune erreur SCSS ni traceback Python.

- [ ] **Step 4 : Commit**

```bash
git add rubicon_addons/sis_document/__manifest__.py
git commit -m "refactor(sis_document): move SCSS to rubicon_frontend"
```

---

## Task 6 : Mettre à jour pdp_frontend

**Files:**
- Modify: `rubicon_addons/pdp_frontend/__manifest__.py`
- Modify: `rubicon_addons/pdp_frontend/static/src/xml/pdp_workspace.xml` (lignes 4, 54, 232, 353)

- [ ] **Step 1 : Ajouter rubicon_frontend aux dépendances**

Dans `__manifest__.py`, modifier le bloc `depends` :

```python
"depends": [
    "web",
    "pdp_base",
    "pdp_price",
    "pdp_picture",
    "rubicon_uom",
    "rubicon_frontend",
],
```

- [ ] **Step 2 : Mettre à jour la div racine (ligne 4)**

Avant :
```xml
<div class="o_action_manager pdp-workspace h-100 w-100 d-flex flex-column" style="font-size: 13px; background: #f0f0f0;">
```

Après :
```xml
<div class="o_action_manager pdp-workspace rbn-workspace h-100 w-100 d-flex flex-column">
```

- [ ] **Step 3 : Mettre à jour la table produits (ligne 54)**

Avant :
```xml
<table class="table table-sm table-hover table-bordered mb-0" style="font-size: 12px;">
```

Après :
```xml
<table class="table table-sm table-hover table-bordered rbn-table mb-0">
```

- [ ] **Step 4 : Mettre à jour la table modals (ligne 232)**

Avant :
```xml
<table class="table table-sm table-bordered table-hover mb-0" style="font-size: 12px;">
```

Après :
```xml
<table class="table table-sm table-bordered table-hover rbn-table mb-0">
```

- [ ] **Step 5 : Mettre à jour le tab-content (ligne 353)**

Avant :
```xml
<div class="tab-content flex-grow-1 p-2 overflow-auto" style="font-size: 12px;">
```

Après :
```xml
<div class="tab-content flex-grow-1 p-2 overflow-auto rbn-table">
```

- [ ] **Step 6 : Vérifier l'upgrade**

```bash
docker compose exec odoo odoo -d rubicon -u pdp_frontend --stop-after-init
```

Expected : aucune erreur, workspace PDP visuellement identique à avant.

- [ ] **Step 7 : Commit**

```bash
git add rubicon_addons/pdp_frontend/__manifest__.py rubicon_addons/pdp_frontend/static/src/xml/pdp_workspace.xml
git commit -m "refactor(pdp_frontend): use rubicon_frontend design tokens"
```

---

## Task 7 : Mettre à jour sis_frontend

**Files:**
- Modify: `rubicon_addons/sis_frontend/static/src/xml/sis_workspace.xml` (lignes 4, 681, 878, 966, 993)

Note : `sis_frontend` dépend de `sis_document` qui dépend maintenant de `rubicon_frontend` — pas besoin de modifier `sis_frontend/__manifest__.py`.

- [ ] **Step 1 : Mettre à jour la div racine (ligne 4)**

Avant :
```xml
<div class="sis-ws h-100 d-flex flex-column" style="font-size:13px; background:#f4f4f4;">
```

Après :
```xml
<div class="sis-ws rbn-workspace h-100 d-flex flex-column">
```

- [ ] **Step 2 : Mettre à jour la table parties (ligne 681)**

Avant :
```xml
<table class="table table-sm table-bordered table-hover mb-0" style="font-size:12px;">
```

Après :
```xml
<table class="table table-sm table-bordered table-hover rbn-table mb-0">
```

- [ ] **Step 3 : Mettre à jour la table bank (ligne 878)**

Avant :
```xml
<table class="table table-sm table-bordered mb-0" style="font-size:12px;">
```

Après :
```xml
<table class="table table-sm table-bordered rbn-table mb-0">
```

- [ ] **Step 4 : Mettre à jour les divs row (lignes 966 et 993)**

Avant (ligne 966) :
```xml
<div class="row g-1 align-items-center" style="font-size:12px;">
```

Après :
```xml
<div class="row g-1 align-items-center rbn-table">
```

Même remplacement pour la ligne 993.

- [ ] **Step 5 : Vérifier l'upgrade**

```bash
docker compose exec odoo odoo -d rubicon -u sis_frontend --stop-after-init
```

Expected : aucune erreur, workspace SIS visuellement identique à avant.

- [ ] **Step 6 : Commit**

```bash
git add rubicon_addons/sis_frontend/static/src/xml/sis_workspace.xml
git commit -m "refactor(sis_frontend): use rubicon_frontend design tokens"
```

---

## Task 8 : Vérification finale

- [ ] **Step 1 : Upgrade complet de tous les modules touchés**

```bash
docker compose exec odoo odoo -d rubicon -u rubicon_frontend,sis_document,pdp_frontend,sis_frontend --stop-after-init
```

Expected : sortie sans erreur, ligne `Modules loaded.` en fin.

- [ ] **Step 2 : Vérification visuelle PDP**

Ouvrir le workspace PDP dans le navigateur. Vérifier :
- Fond de workspace : `#f2f2f2` (légèrement différent de l'ancien `#f0f0f0`, mais cohérent)
- Taille de police tables et contenu : 12px
- Navbar reste noire, boutons primaires noirs

- [ ] **Step 3 : Vérification visuelle SIS**

Ouvrir le workspace SIS dans le navigateur. Vérifier :
- Fond de workspace : `#f2f2f2` (cohérent avec PDP)
- Taille de police : 13px pour le workspace, 12px pour les tables
- Navbar et boutons identiques à PDP

- [ ] **Step 4 : Commit final si nécessaire**

Si des ajustements mineurs ont été faits lors de la vérification :

```bash
git add -p
git commit -m "fix(rubicon_frontend): visual adjustments after verification"
```
