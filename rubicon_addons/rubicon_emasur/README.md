# Rubicon / Emasur Notation

Converts codes between the Rubicon notation and the Emasur one, and carries
the coming system switch: every record keeps its Rubicon `code` and holds the
alternative code next to it — nothing is ever renamed in place, so the whole
history stays searchable under both systems.

## Day-one procedure, when the new system is delivered

1. Load the official codes into the `alt_code` fields of `pdp.product`,
   `pdp.product.model`, `pdp.stone`, `pdp.metal` (CSV import or script). The
   converter (Emasur menu) suggests stone translations; it never invents an
   official code.
2. Complete the mapping tables if the stone vocabulary moved: Emasur menu >
   Stones ("Not mapped yet" filter), Shape Mapping, Legacy Token Aliases.
3. Reindex the history: run `action_backfill_alt_design()` on
   `sis.document.item` (set-wise, seconds, rerunnable after every curation
   round). Only complete conversions are stored.
3bis. Precompute the searchable readings: `action_backfill_alt_code_computed()`
   on `pdp.product` fills `alt_code_computed` — the converter's complete
   reading of each product code, searchable like the historical code but
   never displayed as official.
4. Flip the display: Emasur menu > Notation System (managers). Records with
   no alternative code keep showing their Rubicon code, so a partial load is
   safe. Searching finds records by either code throughout.
5. The PDP workspace filters client-side on `code`: extend its loaded fields
   with `alt_code` when switching for real.

## Adding a third notation system

One Char field on the mixin's inheritors plus one entry in
`emasur.code.mixin.NOTATION_SYSTEMS` — display, search
(`_rec_names_search`) and the switch wizard follow from the registry. The
storage stays one indexed column per system on purpose (fast, importable);
a generic code table would only pay off from several extra systems, which
is not the announced situation.
