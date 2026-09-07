# Rubicon Notation — PDP Bridge

Rubicon-side integration of the shared `rubicon_notation` core (Emasur
runs the core alone; this module is what makes PDP, SIS... use the
notation automatically).

- Links: article ↔ `pdp.stone.type`, notation shape ↔ `pdp.stone.shape`,
  and `rubicon.notation.shade.map` reading a legacy shade as a grade, a
  hue, or both (fused shades like *Pink Light*).
- Services added to `rubicon.notation`: `components_for` /
  `build_token_legacy` (legacy records → token), `transcribe_product`
  (the colour code of a product's real composition, legacy ordering:
  center first then heaviest), `verify_product` (is a written colour
  code coherent with the stones and their order?).
- The wizard gains the **Verify a product** mode.
- `make propose-notation` prefills empty dictionaries from actual usage
  (most-used stones grab the natural letters, defaults from usage,
  grades from the known legacy quality shades). Hues and fused-shade
  mappings are left to human curation. Dev-side and idempotent.
