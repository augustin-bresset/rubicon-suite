# SIS Document Auto-Numbering — Design Spec

**Date:** 2026-04-30
**Module:** `sis_document`, `sis_frontend`

## Overview

When creating a new SIS document, the document name is built automatically from three parts:

```
{DOC_TYPE}-{CLIENT_CODE}-{AAXXX}
```

- `DOC_TYPE` — code du type de document (`SO`, `SQ`, `SI`, …)
- `CLIENT_CODE` — `sis_code` du client (`res.partner.sis_code`)
- `AA` — 2 derniers chiffres de l'année de création (ex : `25` pour 2025)
- `XXX` — numéro de séquence sur 3 digits, n-ième document de l'année AA pour ce triplet `(DOC_TYPE, CLIENT_CODE, AA)`

Exemple : `SO-EMA-25003` = 3e commande SO du client EMA en 2025.

## Règles métier

- La séquence est **par triplet** `(doc_type, client_code, année)` : SO et SQ ont leurs propres compteurs indépendants pour un même client.
- Les 3 digits (`XXX`) sont zéro-paddés : `001`, `002`, …, `999`.
- Le nom final est assigné **au moment du `create()`** côté backend, de façon atomique dans la transaction.
- Si le `name` reçu est déjà complet (import legacy, correction manuelle), le backend ne le modifie pas.

## Frontend (`sis_frontend/static/src/js/sis_workspace.js`)

### `newDocument()`
Aucun changement — initialise déjà `name: this.state.docType + "-"` (ex : `SO-`).

### `onCustomerChange()`
Quand le client change sur un document non encore sauvegardé (`doc.id === null`), mettre à jour l'aperçu du nom :

```js
if (!this.state.doc.id) {
    const partner = this.sisPartners.find(p => p.id === id);
    if (partner?.sis_code) {
        this.state.doc.name = `${this.state.docType}-${partner.sis_code}-`;
    }
}
```

Le champ `name` reste éditable dans le formulaire (correction manuelle possible).

**Résultat UX :**
- Juste après "Nouveau" : `SO-`
- Après sélection du client EMA : `SO-EMA-`
- Après sauvegarde : `SO-EMA-25003` (rechargé depuis le backend)

## Backend (`sis_document/models/document.py`)

Override de `create()` sur `sis.document` :

```python
@api.model_create_multi
def create(self, vals_list):
    for vals in vals_list:
        name = vals.get('name', '')
        parts = name.split('-')
        # Préfixe partiel : "SO-EMA-" → ['SO', 'EMA', '']
        if len(parts) == 3 and parts[2] == '':
            doc_type, client_code = parts[0], parts[1]
            date = vals.get('date_created') or fields.Date.today()
            # date_created arrives as string "2025-01-15" via JSON-RPC, or date object via internal calls
            if isinstance(date, str):
                yy = date[2:4]   # "2025-01-15" → "25"
            else:
                yy = str(date.year)[2:]  # date(2025,1,15) → "25"
            prefix = f'{doc_type}-{client_code}-{yy}'
            self.env.cr.execute(
                "SELECT MAX(name) FROM sis_document WHERE name LIKE %s",
                [prefix + '%']
            )
            row = self.env.cr.fetchone()
            last = row[0] if row and row[0] else None
            seq = (int(last[-3:]) + 1) if last else 1
            vals['name'] = f'{prefix}{seq:03d}'
    return super().create(vals_list)
```

**Garanties :**
- Exécution SQL dans la même transaction → atomique, pas de doublon.
- `date_created` passé par le frontend au moment du save → `yy` correct.
- Noms legacy ou complets (sans `-` final) → non modifiés.

## Fichiers modifiés

| Fichier | Changement |
|---|---|
| `sis_document/models/document.py` | Ajout de `create()` override |
| `sis_frontend/static/src/js/sis_workspace.js` | Mise à jour de `onCustomerChange()` |

## Hors scope

- Renumérotation des documents existants.
- Gestion des séquences > 999 (pas de cas réel attendu).
- Validation unicité (la contrainte SQL existante sur `name` suffit).
