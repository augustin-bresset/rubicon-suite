# Gemstone Notation — PDP Bridge

Rubicon-side integration of the shared `gem_notation` core (Emasur
runs the core alone; this module is what makes PDP, SIS... use the
notation automatically).

- Links: article ↔ `pdp.stone.type`, notation shape ↔ `pdp.stone.shape`,
  and `gem.notation.shade.map` reading a legacy shade as a grade, a
  hue, or both (fused shades like *Pink Light*).
- Services added to `gem.notation`: `components_for` /
  `build_token_legacy` (legacy records → token), `transcribe_product`
  (the colour code of a product's real composition, legacy ordering:
  center first then heaviest), `verify_product` (is a written colour
  code coherent with the stones and their order?).
- The wizard gains the **Verify a product** mode.
- `make propose-notation` prefills the dictionaries from actual usage so
  that EVERY legacy record has a correspondence: stones and shapes get
  2-letter codes (most-used first), grades map the known quality shades,
  every remaining shade is decomposed into hue and/or grade (fused
  labels like *Pink Light* split on the tone word), hues get
  digit+initial codes (Pink → 1P), colour-bearing type names propose the
  article's implied hue, and each article's defaults follow its usage.
  Proposals, not truth — review them in the dictionary screens.
  Dev-side and idempotent.
- The suite's 3-level access policy on the core dictionaries is layered
  on here (the core alone ships read-for-all / admin-full, so it stays
  installable on a bare Odoo).
