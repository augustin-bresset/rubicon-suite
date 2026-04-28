# rubicon_frontend — Design Spec

**Date:** 2026-04-28
**Status:** Approved

## Objectif

Créer un module Odoo technique `rubicon_frontend` qui centralise le thème visuel global de la suite Rubicon (PDP + SIS + futurs workspaces). Résout la divergence de valeurs hardcodées entre les modules existants et fournit une source de vérité unique pour les design tokens.

## Périmètre

- **Inclus :** SCSS uniquement (design tokens, overrides Odoo globaux, classes utilitaires workspace)
- **Exclu :** composants OWL partagés (structures trop variées entre workspaces), helpers JS (à réévaluer quand un besoin concret émergera), menus ou vues Odoo

## Structure du module

```
rubicon_addons/rubicon_frontend/
├── __manifest__.py
└── static/src/scss/
    ├── variables.scss       # design tokens CSS custom properties + variables SCSS Odoo
    ├── odoo_overrides.scss  # overrides thème global Odoo (navbar, boutons, etc.)
    └── workspace.scss       # classes utilitaires .rbn-* pour les workspaces
```

### `__manifest__.py`

- `depends`: `['web']` uniquement
- `application`: `False`
- `assets`:
  - `web._assets_primary_variables`: `variables.scss` (prepend)
  - `web.assets_backend`: `odoo_overrides.scss`, `workspace.scss`

## Design tokens (`variables.scss`)

CSS custom properties déclarées sur `:root`, utilisables dans les templates XML sans recompilation.

| Token | Valeur | Remplace |
|-------|--------|---------|
| `--rbn-brand` | `#000000` | `$o-brand-primary` dans sis_document |
| `--rbn-ws-bg` | `#f2f2f2` | `#f0f0f0` (PDP) / `#f4f4f4` (SIS) |
| `--rbn-toolbar-bg` | `#ffffff` | `bg-white` inline |
| `--rbn-border` | `#cccccc` | `#ccc` dans PDP |
| `--rbn-border-light` | `#dddddd` | `#ddd` dans PDP |
| `--rbn-font-ws` | `13px` | `font-size: 13px` inline PDP et SIS |
| `--rbn-font-table` | `12px` | `font-size: 12px` inline PDP |

Variables SCSS Odoo conservées pour le thème global :

```scss
$o-brand-primary: #000000;
$o-brand-odoo: #000000;
$o-navbar-background-color: #000000;
$o-navbar-color: #ffffff;
$primary: $o-brand-primary;
```

## Classes utilitaires (`workspace.scss`)

```scss
.rbn-workspace { font-size: var(--rbn-font-ws); background: var(--rbn-ws-bg); }
.rbn-toolbar   { background: var(--rbn-toolbar-bg); border-bottom: 1px solid var(--rbn-border); }
.rbn-table     { font-size: var(--rbn-font-table); }
```

## Migrations requises

### `sis_document`

- Supprimer `static/src/scss/variables.scss` et `static/src/scss/style.scss`
- Retirer les entrées assets correspondantes du `__manifest__.py`
- Ajouter `rubicon_frontend` aux `depends`

### `pdp_frontend`

- Ajouter `rubicon_frontend` aux `depends`
- Remplacer dans `pdp_workspace.xml` :
  - `style="background: #f0f0f0"` → `class="rbn-workspace"`
  - `style="font-size: 13px"` → absorbé par `.rbn-workspace`
  - `style="font-size: 12px"` sur les tables → `class="rbn-table"`
  - `border: ... #ccc` → `var(--rbn-border)`

### `sis_frontend`

- Dépend déjà de `sis_document` qui dépendra de `rubicon_frontend` — aucun changement direct requis
- Remplacer `style="background:#f4f4f4"` dans `sis_workspace.xml` → `class="rbn-workspace"`

## Décisions écartées

- **Composants OWL partagés :** futurs workspaces auront des structures variées, abstraction prématurée
- **Helpers JS partagés :** aucun besoin concret identifié, à réévaluer sur le prochain workspace
- **Étendre `pdp_base` :** sémantiquement incorrect pour un thème global (SIS ne devrait pas dépendre de `pdp_base`)
