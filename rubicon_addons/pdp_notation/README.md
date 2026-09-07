# PDP Notation

Grammar engine for the structured colour codation decided in the
2026-09-07 notation study (`meta/report/26-09-07/`). The module ships the
machinery — dictionaries, transcription, reverse lookup, verification —
while the actual code assignments stay a curation decision.

## The token grammar: `PP[G][BB][EE]`

| Block | Width | Charset | Meaning |
|-------|-------|---------|---------|
| `PP`  | 2     | letters | stone article (identity) |
| `G`   | 1     | digit   | quality grade |
| `BB`  | 2     | digit + letter | hue |
| `EE`  | 2     | letters | shape |

Blocks are omitted when they match the article's defaults, so the most
common stones read as 2 characters. The widths and character classes make
every token parse without separators: a lone digit is a grade, a digit
followed by a letter starts a hue, letters are a shape — at most one
split of the remainder is valid.

A colour code joins the distinct stone tokens with `+`, ordered like the
legacy colour code (center stone first, then heaviest single stone
descending, ties by token).

Colour-bearing legacy types (Blue Topaz...) are folded through the
article's *implied hue*: the article is the base species, the hue is
implied by the mapping, and a hue-mapped shade on such a stone is
refused as a double colour.

## Dictionaries

- `pdp.notation.stone` — article code ↔ legacy `pdp.stone.type`, with the
  default shade/shape and the optional implied hue;
- `pdp.notation.grade`, `pdp.notation.hue` — the quality and colour
  vocabularies;
- `pdp.notation.shade.map` — how a legacy shade reads: a grade, a hue, or
  both (fused shades like *Pink Light*);
- `pdp.notation.shape` — shape code ↔ legacy `pdp.stone.shape`.

## Services (`pdp.notation`)

- `parse_token(token)` / `build_token(type, shade, shape)` — both
  directions between tokens and legacy records;
- `transcribe_product(product_id)` — the colour code of a product's real
  composition, ordered;
- `verify_product(product_id, code)` — is a written colour code coherent
  with the composition (stones and order)?
- `lookup(text)` — name or code to dictionary entries, all axes.

The **Transcribe & Verify** wizard (PDP menu → Notation) exposes the three
services interactively.

## Bootstrapping the dictionaries

`make propose-notation` prefills empty dictionaries with frequency-based
proposals (most-used stones grab the natural letters; defaults from
usage; grades from the known legacy quality shades). Hues and fused-shade
mappings are left to human curation. The tool is dev-side on purpose and
idempotent — review the proposals in the dictionary screens afterwards.
