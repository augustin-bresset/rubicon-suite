from odoo.tests.common import TransactionCase

# Troy ounce — the unit precious metals are priced in (see component_metal.py).
OZ_TO_G = 31.1034768


class TestR132CostChecks(TransactionCase):
    """Non-circular cost checks on the R132 reference product.

    The cost table is recomputed on the fly. Rather than pin a snapshot of the
    engine's own output (which only proves it equals itself), this validates
    relationships that must hold for any correct computation: price = cost +
    margin on each line and Net = sum of the lines, plus an independent
    re-derivation of the metal line from the troy-ounce formula.

    Skips when the R132 dataset or the Emasur margin is absent.
    """

    REF_CODE = 'R132-GA+RHO+CT+PF+T/W'

    def setUp(self):
        super().setUp()
        self.product = self.env['pdp.product'].search([('code', '=', self.REF_CODE)], limit=1)
        self.margin = self.env['pdp.margin'].search([('code', '=', 'EMA')], limit=1)
        self.usd = self.env['res.currency'].search([('name', '=', 'USD')], limit=1)
        self.purity = self.env['pdp.metal.purity'].search([('code', '=', '18K')], limit=1)
        if not (self.product and self.margin and self.usd and self.purity):
            self.skipTest("R132 / Emasur / USD / 18K not all present in this database")
        self.res = self.env['pdp.price.service'].compute_price_by_ids(
            self.product.id, self.margin.id, self.usd.id,
            purity_id=self.purity.id, conv_metal_code=False)
        self.lines = {ln['label']: ln for ln in self.res['lines']}

    def test_invariants_hold(self):
        # price = cost + margin on every line, and Net = sum of the lines.
        sc = sm = sp = 0.0
        for ln in self.res['lines']:
            self.assertAlmostEqual(ln['price'], ln['cost'] + ln['margin'], places=2,
                                   msg=f"{ln['label']}: price != cost + margin")
            sc += ln['cost']; sm += ln['margin']; sp += ln['price']
        t = self.res['totals']
        self.assertAlmostEqual(t['cost'], sc, places=2)
        self.assertAlmostEqual(t['margin'], sm, places=2)
        self.assertAlmostEqual(t['price'], sp, places=2)

    def test_metal_line_follows_the_troy_ounce_formula(self):
        """Re-derive the metal cost from first principles (independent check).

        metal_cost = (cost_per_troy_ounce / OZ_TO_G) * alloy_weight * purity_fraction
        """
        metal = self.env['pdp.product.model.metal'].search([
            ('model_id', '=', self.product.model_id.id),
            ('purity_id.code', '=', '18K'),
        ], limit=1)
        self.assertTrue(metal, "no 18K metal weight for R132")
        cost_oz = metal.metal_id.cost                     # USD per troy ounce
        purity_fraction = self.purity.percent / 100.0
        expected = (cost_oz / OZ_TO_G) * metal.weight * purity_fraction
        # conv_metal_code is False, so the merged 'metal' line is pure metal.
        self.assertAlmostEqual(self.lines['Metal']['cost'], expected, delta=0.1,
                               msg="metal line does not match the troy-ounce formula")
