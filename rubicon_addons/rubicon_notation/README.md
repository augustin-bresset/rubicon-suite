# Rubicon Notation

An **independent stone referential** — think of it as a standalone
counterpart of `pdp_stone`: its own catalogue of stone identities,
grades, hues and shapes, where selecting a stone's components gives its
code and a code reads back into its components. It implements the
structured colour codation decided in the 2026-09-07 notation study
(`meta/report/26-09-07/`).

It is **not a translation layer**: the Rubicon-Emasur code conversion is
`rubicon_emasur`'s job. This module depends on no company data, so
either company runs it as-is; the optional wiring to the PDP stone data
(transcription of real compositions, order verification, usage-based
proposals) lives in `rubicon_notation_pdp`.

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

A colour code joins the distinct stone tokens with `+`, ordered center
stone first, then heaviest single stone descending (ties by token).

An article carrying a colour in its identity (Blue Topaz...) declares an
*implied hue*: the dictionary holds no colour+species compound and
writing another hue on such an article is refused as a double colour.

## Contents

- Dictionaries: `rubicon.notation.stone` (articles, with implied hue and
  notation-level defaults), `.grade`, `.hue`, `.shape`.
- Services (`rubicon.notation`): `parse_token`, `build_token`,
  `order_tokens`, `transcribe` (from notation components), `lookup`.
- The **Transcribe & Verify** wizard under the top-level Notation menu
  (parse a code, look up a name or code; bridge modules add their own
  modes).
