# Pictures Database — Detailed Audit Report

**Source:** `Pictures.bak` (SQL Server 2019, ~3.2 GB)  
**Restored into:** Docker container `sqlsrv_pics`  
**Report date:** 2026-04-06  
**Purpose:** Assess content, quality, and importability of the legacy image database before re-importing into `pdp.picture` (Odoo 18).

---

## Important: Drawing Reference Codes (e.g. RP128B)

The Pictures database **does not contain drawing reference codes** such as `RP128B`. These codes are stored in a completely separate source — the `Models.csv` file imported during the initial Odoo data load — and are persisted in the `pdp.product.model.drawing` field in Odoo.

The Pictures database only knows that a model (e.g. `R132`) has a binary photo and optionally a binary technical drawing image (`Sketch` column). It does not record the design reference number associated with that drawing.

| Information | Source |
|---|---|
| Model photo (binary image) | `Pictures.bak` → `Sketches.Picture` |
| Technical drawing (binary image) | `Pictures.bak` → `Sketches.Sketch` |
| Drawing reference code (`RP128B`) | `Models.csv` → `pdp.product.model.drawing` |

The two data sources are joined solely by the model code (e.g. `R132`). There is no cross-reference or foreign key between them.

---

## Database Schema

The database `PICTURES` contains 4 tables in the `dbo` schema:

| Table | Role | Rows |
|---|---|---|
| `Sketches` | Model-level photos + technical drawings (primary source) | 10 656 |
| `TSketches` | Additional model photos (same schema as Sketches) | 2 |
| `Snapshots` | Product-specific photos (stone + gold variant) | 250 |
| `dtproperties` | SQL Server internal metadata (empty, unused) | 0 |

### Column definitions

| Table | Column | Type | Nullable | Description |
|---|---|---|---|---|
| Sketches | CatID | char(2) | NO | Category prefix (R, E, QU, P, N…) |
| Sketches | OrnID | char(5) | NO | Model number within category |
| Sketches | Model | varchar(7) | YES | Computed model code (= CatID+OrnID, always set) |
| Sketches | Picture | image | YES* | Model photo (stored as binary blob) |
| Sketches | Sketch | image | YES | Technical drawing (optional) |
| Sketches | LastUpdated | datetime | NO | Last modification timestamp |
| Snapshots | CatID | char(2) | NO | Category prefix |
| Snapshots | OrnID | char(5) | NO | Model number |
| Snapshots | StoneID | varchar(14) | NO | Stone composition code (2002 nomenclature) |
| Snapshots | GoldID | varchar(4) | NO | Metal color code (W=white, Y=yellow) |
| Snapshots | Picture | image | YES* | Product-specific photo |
| Snapshots | LastUpdated | datetime | NO | Last modification timestamp |
| TSketches | CatID | char(2) | NO | Same schema as Sketches |
| TSketches | OrnID | char(5) | NO | — |
| TSketches | Model | varchar(7) | YES | — |
| TSketches | Picture | image | YES* | Higher-resolution model photo |
| TSketches | Sketch | image | YES | Technical drawing (none present) |
| TSketches | LastUpdated | datetime | NO | — |

> *`Picture` is declared `NOT NULL` in DDL but photos with `DATALENGTH = 0` do exist (28 in Sketches).

---

## Table: `Sketches`

### Global statistics

| Metric | Value |
|---|---|
| Total rows | 10 656 |
| Photos present (`DATALENGTH > 0`) | 10 628 |
| Photos empty (null/zero-length) | 28 |
| Technical drawings present | 275 |
| Technical drawings absent (NULL) | 2 396 |
| Rows without any Model value | 0 |
| Date range | 1980-01-04 → 2024-09-04 |
| Average photo size | ~138 KB |
| Minimum photo size | 0 B (empty) |
| Maximum photo size | 1 881 153 B (~1.8 MB, model Z1) |

### Sample rows (most recently updated)

| Model | Photo (B) | Drawing (B) | Last Updated |
|---|---|---|---|
| R2138 | 93 714 | — | 2024-09-04 |
| R2137 | 103 215 | — | 2024-09-03 |
| E1692 | 119 780 | — | 2024-09-03 |
| E1691 | 134 263 | — | 2024-09-03 |
| BA313 | 84 448 | — | 2024-08-28 |
| QU6217 | 708 122 | 708 122 | 2009-10-16 |
| BQ204 | 100 303 | 999 996* | 2018-03-01 |
| N405D | 223 632 | 999 996* | 2022-09-21 |

*Truncated — see inconsistencies section.

### Coverage by category

| Category | Rows | Photos | Drawings | Oldest Entry | Newest Entry | Avg Photo (KB) |
|---|---|---|---|---|---|---|
| R (rings) | 2 879 | 2 877 | 20 | 1980-01-04 | 2024-09-04 | 130 |
| E (earrings) | 2 364 | 2 364 | 3 | 1980-01-04 | 2024-09-03 | 144 |
| QU | 1 711 | 1 685 | **234** | 2003-07-01 | 2024-04-10 | 121 |
| P (pendants) | 1 494 | 1 494 | 4 | 1980-01-04 | 2024-08-27 | 144 |
| N (necklaces) | 735 | 735 | 7 | 1980-01-04 | 2024-08-22 | 154 |
| BA | 409 | 409 | 0 | 1980-01-04 | 2024-08-28 | 135 |
| SP | 307 | 307 | 5 | 2007-02-28 | 2024-08-16 | 149 |
| SL | 233 | 233 | 1 | 2002-11-16 | 2010-02-12 | 73 |
| B (bracelets) | 218 | 218 | 0 | 1980-01-04 | 2024-08-13 | 149 |
| CF | 124 | 124 | 0 | 1980-01-04 | 2023-11-08 | 109 |
| BR | 83 | 83 | 0 | 1980-01-04 | 2024-03-28 | 112 |
| PF | 31 | 31 | 0 | 1980-01-04 | 2005-05-18 | 177 |
| BT | 17 | 17 | 0 | 2004-08-24 | 2023-05-12 | 158 |
| TP | 12 | 12 | 0 | 2010-04-22 | 2018-08-15 | 206 |
| PP | 10 | 10 | 0 | 2004-04-08 | 2005-06-28 | 241 |
| *(other)* | ~24 | ~24 | 1 | — | — | — |

> **Note on QU:** This category concentrates 85% of all technical drawings (234/275). These are likely quota or special-series models.

### Update activity by year

| Year | Records Updated | With Drawings |
|---|---|---|
| 2024 | 409 | 1 |
| 2023 | 521 | 3 |
| 2022 | 247 | 17 |
| 2021 | 339 | 4 |
| 2020 | 276 | 3 |
| 2019 | 412 | 0 |
| 2018 | 379 | 7 |
| 2017 | 428 | 2 |
| 2016 | 316 | 0 |
| 2015 | 419 | 0 |
| 2014 | 389 | 3 |
| 2013 | 855 | 3 |
| 2012 | 448 | 0 |
| 2011 | 498 | 22 |
| 2010 | 586 | 7 |
| 2009 | 647 | **192** |
| 2008 | 636 | 9 |
| 2007 | 433 | 2 |
| 2006 | 270 | 0 |
| 2005 | 510 | 0 |
| 2004 | 362 | 0 |
| 2003 | 321 | 0 |
| 2002 | 744 | 0 |
| 1980 | 211 | 0 |

> The database is **actively maintained** as of September 2024. The 1980 entries reflect the original digitisation batch.

### Inconsistencies and anomalies

| Issue | Count | Details |
|---|---|---|
| Empty photos (`DATALENGTH = 0`) | **28** | 26 in QU, 2 in R — probably models awaiting a photo |
| Technical drawings truncated at 999 996 B | **4** | `BQ204`, `N405D`, `R1876B`, `R2078` — hit SQL Server 1 MB image column limit |
| `Model` field mismatch vs `CatID+OrnID` | **0** | `Model` is fully redundant and consistent across all 10 656 rows |
| `Model` field NULL | **0** | — |
| Photo and drawing identical size (suspicious duplicate) | **190** | 180 in QU — the same binary is stored twice in both columns for these rows |

> The 190 same-size pairs in QU suggest a data-entry practice of copying the photo into the drawing field when no distinct drawing existed.

### Largest photos

| Model | Size (B) | Notes |
|---|---|---|
| Z1 | 1 881 153 | Exceptional — 13× the average |
| P1440C | 1 184 440 | — |
| SL089 | 1 091 000 | — |
| QU6249 | 999 996 | Truncated (1 MB limit) |
| QU6250 | 999 996 | Truncated (1 MB limit) |

### Odoo match rate

| Result | Count | % |
|---|---|---|
| Model found in `pdp.product.model` | 10 181 | **95.7%** |
| No match (discontinued models) | 447 | 4.2% |
| Recoverable via zero-padding (`CF1` → `CF001`) | 14 | 0.1% |

---

## Table: `Snapshots`

### Global statistics

| Metric | Value |
|---|---|
| Total rows | 250 |
| Photos present | 250 (100%) |
| Distinct models (`CatID+OrnID`) | 210 |
| Distinct stone codes (`StoneID`) | 68 |
| Distinct gold codes (`GoldID`) | 2 (W, Y) |
| Date range | 2002-03-13 → 2003-02-18 |
| Average photo size | ~22 KB |
| Minimum photo size | 3 376 B |
| Maximum photo size | 109 133 B |

> **Important:** All data was captured in a **two-month window (2002–2003)**. This table is frozen and no longer maintained.

### Sample rows

| Model | Stone | Gold | Photo (B) | Last Updated |
|---|---|---|---|---|
| R784 | SAPL | W | 10 733 | 2002-03-13 |
| R765 | PEARL | W | 17 168 | 2002-03-13 |
| R765 | D | W | 17 168 | 2002-03-13 |
| E414 | EMCS+CITA | W | 36 453 | 2002-03-13 |
| E414 | GA | W | 36 453 | 2002-03-13 |
| E414 | DTS | W | 36 453 | 2002-03-13 |
| PF016 | L.TSA+DTS | W | 12 518 | 2003-02-18 |

### Coverage by category

| Category | Rows | Distinct Models | Distinct Stones | Avg Photo (KB) |
|---|---|---|---|---|
| R (rings) | 151 | 116 | 53 | 23 |
| P (pendants) | 55 | 55 | 19 | 13 |
| E (earrings) | 39 | 35 | 20 | 28 |
| B (bracelets) | 3 | 2 | 3 | 46 |
| PF | 2 | 2 | 2 | 12 |

### Top 15 stone codes

| Stone | Occurrences | Notes |
|---|---|---|
| D | 28 | Diamond |
| PEARL | 23 | Pearl |
| AQUA | 19 | Aquamarine |
| BTA | 11 | — |
| AM | 10 | Amethyst |
| EMCS | 9 | Emerald-cut stone |
| IOL | 9 | — |
| RUCS | 8 | — |
| DTS | 7 | — |
| ONYX | 7 | Onyx |
| CITA | 6 | Citrine |
| GA | 6 | Garnet |
| SAPL | 6 | Sapphire |
| SKDF | 6 | — |
| AM+PER | 5 | Amethyst + Pearl |

### Gold color distribution

| GoldID | Rows | % |
|---|---|---|
| W (white) | 249 | 99.6% |
| Y (yellow) | 1 | 0.4% |

### Models with multiple variants

| Model | Variants |
|---|---|
| E414 | 3 |
| R645 | 3 |
| R600 | 2 |
| R619 | 2 |
| R655 | 2 |
| R663 | 2 |
| R664 | 2 |
| R660 | 2 |
| R675 | 2 |
| R676 | 2 |

### Inconsistencies and anomalies

| Issue | Count | Details |
|---|---|---|
| Duplicate product key (`CatID+OrnID+StoneID+GoldID`) | **0** | No duplicates |
| Photos very small (< 5 KB, possible corrupt) | **2** | `R435C/AQUA/W` (3 376 B), `PF015/DTS/W` (and one other) |
| Models present in Snapshots but absent from Sketches | **15** | See list below |
| Stone codes matching current Odoo product codes | ~18% | 82% miss — stone nomenclature is from 2002 |

### Models in Snapshots not found in Sketches

These 15 product photos have no corresponding model photo in Sketches:

| Model | Stone | Gold | Photo (B) |
|---|---|---|---|
| E013B | SACS | W | 36 453 |
| E018A | PEARL | W | 22 773 |
| E346 | DTS | W | 43 021 |
| P030 | MABE | W | 17 574 |
| R422B | D | W | 11 395 |
| R435C | AQUA | W | 3 376 |
| R552 | AM | W | 18 336 |
| R552 | BTA | W | 18 336 |
| R655 | D | W | 43 187 |
| R655 | NEW+SACS | W | 43 187 |
| R687B | PEARL | W | 58 812 |
| R692 | IOL+RHO | W | 26 386 |
| R707 | MOP | W | 20 151 |
| R708 | MOP1 | W | 14 336 |
| R711 | SAOC | W | 32 019 |

### Odoo match rate

| Strategy | Count | % |
|---|---|---|
| Exact product code match | ~45 | 18% |
| Fallback to model scope (model exists in Odoo) | ~167 | 67% |
| Truly unresolvable (model also absent from Odoo) | ~38 | 15% |

> The 82% miss rate on exact product codes is due to stone nomenclature from 2002 that does not match current Odoo product codes (e.g. `PEARL` vs current stone code format). The recommended import strategy is to fall back to model-scope attachment when no exact product match exists.

---

## Table: `TSketches`

### Global statistics

| Metric | Value |
|---|---|
| Total rows | **2** |
| Photos present | 2 (100%) |
| Technical drawings present | 0 |
| Date range | 2022-09-16 → 2022-09-20 |
| Average photo size | ~1.8 MB |
| Minimum photo size | 1 184 655 B (~1.2 MB) |
| Maximum photo size | 2 413 747 B (~2.4 MB) |

### Full content with Sketches comparison

| Model | TSketches Photo (B) | Sketches Photo (B) | Size Ratio | Last Updated |
|---|---|---|---|---|
| E1514C | 1 184 655 | 254 474 | **×4.7** | 2022-09-16 |
| P761 | 2 413 747 | 160 177 | **×15.1** | 2022-09-20 |

### Interpretation

TSketches contains **high-resolution replacements** for two models already present in Sketches. Both entries were added in September 2022, likely as part of a quality upgrade. Neither has a technical drawing.

**Import rule:** For models `E1514C` and `P761`, the TSketches photo must take **priority over** the Sketches photo during import, as it is significantly larger and of higher quality.

---

## Table: `dtproperties`

This table is a SQL Server Enterprise Manager internal metadata table. It contains **0 rows** and carries no business data. It can be ignored entirely during import.

---

## Cross-table analysis

### Overlap between Sketches and Snapshots

| Category | In Sketches | In Snapshots | In Both | Snapshots-only |
|---|---|---|---|---|
| R | 2 879 | 116 distinct models | 101 | 15 |
| P | 1 494 | 55 | 55 | 0 |
| E | 2 364 | 35 | 27 | 8 |
| B | 218 | 2 | 2 | 0 |
| PF | 31 | 2 | 2 | 0 |

### Unique model codes across all tables

| Source | Model codes |
|---|---|
| Sketches | 10 656 |
| TSketches | 2 (both overlap with Sketches) |
| Snapshots | 210 (all are subsets of Sketches categories) |
| **Unique total** | **10 656** |

---

## Import summary for Odoo (`pdp.picture`)

| Source | Exportable records | Expected Odoo matches | Scope in Odoo |
|---|---|---|---|
| Sketches — photos | 10 628 | ~10 195 (95.7%) | `model` |
| Sketches — drawings | 275 (4 truncated) | ~262 | `model` (drawing field) |
| TSketches — photos | 2 (high-res replacements) | 2 | `model` (priority over Sketches) |
| Snapshots — exact product | ~45 | ~45 | `product` |
| Snapshots — model fallback | ~167 | ~167 | `model` (fallback) |
| Snapshots — unresolvable | ~38 | 0 | lost |
| **Total importable** | **~10 908** | **~10 671** | — |

### Known data quality issues requiring attention

1. **4 truncated drawings** (`BQ204`, `N405D`, `R1876B`, `R2078`): all stored at exactly 999 996 B due to SQL Server's legacy 1 MB `image` column limit. The original files may be larger but are irrecoverably truncated in this backup.
2. **28 empty model photos**: 26 in QU, 2 in R. These are placeholder rows with no binary content.
3. **190 identical photo/drawing pairs** in Sketches (180 in QU): the same binary is stored in both `Picture` and `Sketch`. These are valid photos repurposed as drawings — not errors.
4. **Snapshots stone codes obsolete**: the `StoneID` values in Snapshots (PEARL, AQUA, EMCS, etc.) predate the current Odoo stone taxonomy. No direct product-code match is possible for the majority of rows.
5. **Two models (E1514C, P761) in TSketches**: the import must prefer the TSketches version to avoid overwriting high-resolution photos with lower-resolution Sketches equivalents.
