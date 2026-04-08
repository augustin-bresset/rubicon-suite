Voici votre texte réécrit proprement en Markdown avec la version anglaise, sans reformulation ni ajouts :

---

# Vue d'ensemble / Overview

| Table        | Rôle / Role                                                                                              | Lignes / Rows |
| ------------ | -------------------------------------------------------------------------------------------------------- | ------------- |
| Sketches     | Photos modèle + dessins techniques (source principale) / Model photos + technical drawings (main source) | 10 656        |
| TSketches    | Photos modèle complémentaires (même schéma) / Complementary model photos (same schema)                   | 2             |
| Snapshots    | Photos spécifiques produit (variant stone/gold) / Product-specific photos (stone/gold variant)           | 250           |
| dtproperties | Métadonnées internes SQL Server (inutile) / Internal SQL Server metadata (unused)                        | —             |

---

# Sketches — Photos modèle / Model Photos

## Couverture générale / Overall coverage

* 10 628 photos présentes (DATALENGTH > 0) sur 10 656 lignes / 10,628 photos present (DATALENGTH > 0) out of 10,656 rows
* 28 entrées sans photo (null ou vide) — essentiellement la catégorie QU / 28 entries without photo (null or empty) — mainly category QU
* 275 dessins techniques (Sketch) présents / 275 technical drawings (Sketch) present
* 4 dessins tronqués à exactement 999 996 octets : BQ204, N405D, R1876B, R2078 — artefact de limite SQL Server (1 Mo) / 4 truncated drawings at exactly 999,996 bytes: BQ204, N405D, R1876B, R2078 — SQL Server limit artifact (1 MB)

## Tailles des photos / Photo sizes

* Min : ~0 KB (corrompu) / Min: ~0 KB (corrupted)
* Max : ~1,8 MB / Max: ~1.8 MB
* Moyenne : ~138 KB / Average: ~138 KB

## Plage temporelle (LastUpdated) / Time range (LastUpdated)

* Plus ancienne : 1980 / Oldest: 1980
* Plus récente : 2024-09-04 / Most recent: 2024-09-04
* La base est activement maintenue jusqu'en 2024 / Database actively maintained until 2024

## Répartition par catégorie / Distribution by category

| CatID             | Lignes / Rows | Photos | Dessins / Drawings | Notes                                              |
| ----------------- | ------------- | ------ | ------------------ | -------------------------------------------------- |
| R                 | 2 879         | 2 879  | 20                 | Bagues, catégorie dominante / Rings, main category |
| E                 | 2 364         | 2 364  | 3                  |                                                    |
| QU                | 1 711         | ~1 683 | 234                | Forte densité de dessins / High drawing density    |
| P                 | 1 494         | 1 494  | 4                  |                                                    |
| N                 | 735           | 735    | 7                  |                                                    |
| BA                | 409           | 409    | 0                  |                                                    |
| SP                | 307           | 307    | 5                  |                                                    |
| (autres / others) | ~757          | ~757   | ~2                 | CF, BQ, T_, etc.                                   |

* Champ Model : vérifié sur 10 656 lignes — Model = RTRIM(CatID) + RTRIM(OrnID) à 100 %. Aucune divergence. / Model field: checked on 10,656 rows — Model = RTRIM(CatID) + RTRIM(OrnID) at 100%. No divergence.
* Le champ est redondant mais fiable. / Field is redundant but reliable.

## Correspondance avec Odoo / Odoo matching

* 10 181 / 10 628 photos (95%) ont un code modèle qui existe dans pdp.product.model / 10,181 / 10,628 photos (95%) have a model code existing in pdp.product.model
* 447 non-matchés = modèles anciens/discontinués absents d'Odoo / 447 non-matched = old/discontinued models missing in Odoo
* 14 récupérables par zero-padding (CF1 → CF001) / 14 recoverable by zero-padding (CF1 → CF001)

---

# Sketches — Dessins techniques / Technical Drawings

| Statut / Status                                               | Nombre / Count |
| ------------------------------------------------------------- | -------------- |
| Dessins présents et valides / Valid drawings                  | 271            |
| Dessins tronqués (999 996 B) / Truncated drawings (999,996 B) | 4              |
| Total                                                         | 275            |

* Les dessins sont concentrés sur QU (234/275 = 85 %). / Drawings concentrated in QU (234/275 = 85%)
* Les catégories R, E, P, N, SP n'ont que quelques dessins chacune. / Categories R, E, P, N, SP have only a few drawings each

---

# Snapshots — Photos produit-spécifiques / Product-Specific Photos

## Couverture générale / Overall coverage

* 250 lignes, toutes avec photo (Picture IS NOT NULL) / 250 rows, all with photo (Picture IS NOT NULL)
* Données datant uniquement de 2002–2003 — snapshot figé, plus mis à jour / Data only from 2002–2003 — snapshot frozen, no longer updated

## Clés de composition / Composition keys

* GoldID : W = 249, Y = 1 (quasi-exclusivement or blanc / almost exclusively white gold)
* 68 StoneID distincts / 68 distinct StoneIDs
* 210 modèles uniques représentés / 210 unique models represented

## Top pierres (StoneID) / Top stones

| StoneID                   | Occurrences |
| ------------------------- | ----------- |
| D (diamant / diamond)     | 28          |
| PEARL                     | 23          |
| AQUA                      | 19          |
| BTA                       | 11          |
| AM (améthyste / amethyst) | 10          |
| EMCS+CITA                 | 9           |
| (autres / others)         | ~150        |

* Les codes pierres sont en nomenclature 2002 (PEARL, AGATE, EMCS+CITA...) — incompatibles avec les codes produits Odoo actuels. / Stone codes in 2002 nomenclature — incompatible with current Odoo product codes

## Répartition par catégorie / Distribution by category

| CatID              | Photos |
| ------------------ | ------ |
| R (bagues / rings) | 151    |
| P                  | 55     |
| E                  | 39     |
| B                  | 3      |
| PF                 | 2      |

* Modèles avec plusieurs variantes / Models with multiple variants

  * 38 modèles ont ≥ 2 variantes dans Snapshots / 38 models have ≥ 2 variants in Snapshots
  * E414 et R645 ont 3 variantes chacun / E414 and R645 have 3 variants each

## Taux de correspondance avec Odoo / Odoo matching rate

* Par code produit exact : 18 % (82 % de miss — codes pierres obsolètes) / By exact product code: 18% (82% miss — obsolete stone codes)
* Fallback possible (modèle existant dans Odoo) : 167/205 misses → 81 % / Fallback possible (model exists in Odoo): 167/205 misses → 81%
* 38 produits dont le modèle n'existe plus dans Odoo : perdus définitivement / 38 products whose model no longer exists in Odoo: lost permanently

---

# TSketches — Photos complémentaires haute résolution / High-Resolution Complementary Photos

* Seulement 2 lignes / Only 2 rows

| Code modèle / Model code | Taille dans TSketches / Size in TSketches | Taille dans Sketches / Size in Sketches | Delta                         |
| ------------------------ | ----------------------------------------- | --------------------------------------- | ----------------------------- |
| E1514C                   | 1,18 MB                                   | 254 KB                                  | ×4,6 plus grand / ×4.6 larger |
| P761                     | 2,41 MB                                   | 160 KB                                  | ×15 plus grand / ×15 larger   |

* Ces deux entrées sont des doublons améliorés — même modèle que dans Sketches, mais résolution nettement supérieure. / These two entries are enhanced duplicates — same model as in Sketches, but much higher resolution
* L'import doit préférer TSketches pour ces deux modèles. / Import should prefer TSketches for these two models

---

# Synthèse pour l'import Odoo / Summary for Odoo Import

| Catégorie / Category                | Fichiers exportables / Exportable files       | Matchs Odoo attendus / Expected Odoo matches                        |
| ----------------------------------- | --------------------------------------------- | ------------------------------------------------------------------- |
| Photos modèle (Sketches)            | 10 628                                        | ~10 181 (95%)                                                       |
| Dessins (Sketches)                  | 275 (dont 4 tronqués / including 4 truncated) | ~262                                                                |
| Photos produit (Snapshots)          | 250                                           | ~45 directs + 167 fallback modèle / ~45 direct + 167 fallback model |
| Photos haute résolution (TSketches) | 2                                             | 2 (remplacement E1514C et P761 / replacement E1514C and P761)       |

* Import actuel : seulement 5 641 photos modèle importées sur ~10 181 possibles (55%). / Current import: only 5,641 model photos imported out of ~10,181 possible (55%)
* Le re-run de make import-pictures après nettoyage des orphelins devrait monter à ~95%. / Re-run of make import-pictures after cleaning orphans should reach ~95%

---

# Notes finales / Final notes

* Ce rapport est basé sur les données extraites directement de la BAK SQL Server restaurée. / This report is based on data extracted directly from the restored SQL Server BAK.
* Les 447 modèles sans correspondance Odoo sont des modèles hors catalogue — aucune action corrective n'est possible sans les réintégrer dans Odoo. / The 447 models without Odoo match are out-of-catalog models — no corrective action possible without reintegrating into Odoo.

