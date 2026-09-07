# PDP Product

Products, models and stone compositions of the Product Design Process.

## How the product code is computed

A structured product code reads `{MODEL}-{COLORS}/{METAL}`, e.g.
`B012-AM+PER/W`.

### The colour segment

`compute_color_code()` (on `pdp.product.stone.composition`) derives the
COLORS segment from the actual stone lines. The segment joins the
**distinct stone TYPE codes** with `+`, ordered by this rule:

1. the **center stone**'s type comes first (the line flagged `is_center`;
   at most one line per composition carries the flag);
2. the remaining types follow by **heaviest single stone, descending** —
   the weight compared is the largest `weight` among the lines of that
   type, not the sum;
3. ties are broken by type code, ascending, so the result is
   deterministic.

A type appearing on several lines is written once. Shades and shapes are
not part of the colour segment (a change under study — see the notation
work in `rubicon_emasur`).

### Suggestion, never rewriting

`compute_suggested_code()` builds the full `{MODEL}-{COLORS}/{METAL}`
suggestion without ever writing it. The workspace shows the suggestion
under the selected product when it differs from the stored code.

`apply_suggested_code()` is the only writer, per-record and opt-in:

- it refuses an empty suggestion or one already used by another product;
- the previous code is preserved in `legacy_code`, which stays searchable
  (`_rec_names_search`), so historical references keep finding the
  renamed product;
- the composition's own code is realigned to `{MODEL}-{COLORS}`.

Legacy codes are never rewritten in bulk.

### Uniqueness and deletion

Product codes are unique (constraint + duplicate check in
`apply_suggested_code`). Deleting a product model with products still
attached is refused unless the `rubicon_force_delete` context key is set.
