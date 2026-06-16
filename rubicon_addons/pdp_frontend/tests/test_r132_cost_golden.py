from odoo.tests.common import TransactionCase

# Troy ounce — the unit precious metals are priced in (see component_metal.py).
OZ_TO_G = 31.1034768


class TestR132CostGolden(TransactionCase):
    """Golden-master of the R132 cost table (see meta/pdp/smoke_test.md).

    The product cost table is never stored — it is recomputed on the fly — so
    this test pins the *current* output of pdp.price.service for the R132
    reference product (margin Emasur, 18K, USD). Its job is to guarantee the
    pricing formulas keep producing the same figures (regression guard), and
    to re-derive the metal line from first principles so a change to the
    formula or to the ounce constant is caught.

    These numbers differ from the old-PDP capture in smoke_test.md on purpose:
    e.g. Metal is 690.69 here vs 758.45 there because the engine now prices in
    troy ounces (31.10 g) instead of standard ounces (28.35 g) — the correct
    unit for precious metals. Update the golden values only when a reference
    price/rate/margin is changed deliberately.

    Skips when the R132 dataset or the Emasur margin is absent.
    """

    REF_CODE = 'R132-GA+RHO+CT+PF+T/W'

    # (cost, margin, price) per line, current engine output, margin = Emasur.
    GOLDEN = {
        'Metal':     (690.69, 124.32, 815.01),
        'Stone':     (114.72,  20.90, 135.62),
        'Setting':   (22.93,   59.04,  81.97),
        'Recutting': (7.80,     0.00,   7.80),
        'Labor':     (16.72,   43.05,  59.77),
        'Misc':      (8.00,     7.96,  15.96),
        'Parts':     (0.00,     0.00,   0.00),
    }
    GOLDEN_NET = (860.86, 255.27, 1116.13)

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

    def test_cost_table_matches_golden(self):
        for label, (cost, margin, price) in self.GOLDEN.items():
            self.assertIn(label, self.lines, f"missing cost line {label}")
            ln = self.lines[label]
            self.assertAlmostEqual(ln['cost'], cost, places=2, msg=f"{label} cost")
            self.assertAlmostEqual(ln['margin'], margin, places=2, msg=f"{label} margin")
            self.assertAlmostEqual(ln['price'], price, places=2, msg=f"{label} price")

    def test_net_totals_match_golden(self):
        cost, margin, price = self.GOLDEN_NET
        t = self.res['totals']
        self.assertAlmostEqual(t['cost'], cost, places=2)
        self.assertAlmostEqual(t['margin'], margin, places=2)
        self.assertAlmostEqual(t['price'], price, places=2)

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
