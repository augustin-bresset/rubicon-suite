from odoo.tests.common import TransactionCase

# Troy ounce, as used by the metal component.
OZ_TO_G = 31.1034768


class TestPriceTableGolden(TransactionCase):
    """End-to-end golden test of the full cost table on a synthetic product.

    Every input is a round number in a single currency (USD), so the whole
    cost / margin / price table can be derived by hand and asserted exactly,
    with no dependency on live data or exchange rates. This guards the
    pricing formulas as a whole (the per-component tests cover them in
    isolation).

    Derivation (margin rates: metal x1.2, labor x1.4 via labor_metal_rate,
    misc x1.5):

        Metal cost  = (3110.34768 / 31.1034768) * 10 g * 50%  = 100 * 5 = 500.00
        Metal margin= (1.2 - 1) * 500                                    = 100.00
        Labor cost  = 50.00 (USD, no conversion)
        Labor margin= (1.4 - 1) * 50                                     = 20.00
        Misc cost   = 10.00
        Misc margin = (1.5 - 1) * 10                                     = 5.00
        No stones / setting / recutting / parts                          = 0
        Net         = 560.00 cost / 125.00 margin / 685.00 price
    """

    EXPECTED = {
        'Metal':     (500.00, 100.00, 600.00),
        'Stone':     (0.00,     0.00,   0.00),
        'Setting':   (0.00,     0.00,   0.00),
        'Recutting': (0.00,     0.00,   0.00),
        'Labor':     (50.00,   20.00,  70.00),
        'Misc':      (10.00,    5.00,  15.00),
        'Parts':     (0.00,     0.00,   0.00),
    }
    EXPECTED_NET = (560.00, 125.00, 685.00)

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        env = cls.env
        cls.usd = env.ref('base.USD')

        cls.purity = env['pdp.metal.purity'].create({'code': 'GOLD50', 'percent': 50.0})
        # 3110.34768 USD / troy ounce == exactly 100 USD / gram.
        cls.metal = env['pdp.metal'].create({
            'code': 'GTST', 'name': 'Golden Test Metal',
            'cost_method': 'fixed', 'cost': OZ_TO_G * 100, 'currency_id': cls.usd.id,
        })
        cls.model = env['pdp.product.model'].create({'code': 'GTSTMOD'})
        cls.product = env['pdp.product'].create({
            'code': 'GTSTPROD', 'model_id': cls.model.id, 'metal': 'W',
        })
        env['pdp.product.model.metal'].create({
            'model_id': cls.model.id, 'metal_id': cls.metal.id,
            'purity_id': cls.purity.id, 'weight': 10.0, 'metal_version': 'W',
        })

        cls.margin = env['pdp.margin'].create({
            'code': 'GTSTMG', 'name': 'Golden Test Margin',
            'labor_metal_rate': 1.4, 'labor_stone_rate': 1.0,
        })
        env['pdp.margin.metal'].create({
            'margin_id': cls.margin.id, 'metal_purity_id': cls.purity.id, 'rate': 1.2,
        })

        labor_type = env['pdp.labor.type'].create({'code': 'GLAB', 'name': 'Golden Labor'})
        env['pdp.labor.cost.model'].create({
            'model_id': cls.model.id, 'labor_id': labor_type.id, 'metal': 'W',
            'cost': 50.0, 'currency_id': cls.usd.id,
        })

        addon_type = env['pdp.addon.type'].create({'code': 'GADD', 'name': 'Golden Addon'})
        env['pdp.addon.cost'].create({
            'product_id': cls.product.id, 'addon_id': addon_type.id,
            'cost': 10.0, 'currency_id': cls.usd.id,
        })
        env['pdp.margin.addon'].create({
            'margin_id': cls.margin.id, 'addon_id': addon_type.id, 'rate': 1.5,
        })

    def setUp(self):
        super().setUp()
        self.res = self.env['pdp.price.service'].compute_price_by_ids(
            self.product.id, self.margin.id, self.usd.id, purity_id=self.purity.id)
        self.lines = {ln['label']: ln for ln in self.res['lines']}

    def test_full_table(self):
        for label, (cost, margin, price) in self.EXPECTED.items():
            self.assertIn(label, self.lines, f"missing line {label}")
            ln = self.lines[label]
            self.assertAlmostEqual(ln['cost'], cost, places=2, msg=f"{label} cost")
            self.assertAlmostEqual(ln['margin'], margin, places=2, msg=f"{label} margin")
            self.assertAlmostEqual(ln['price'], price, places=2, msg=f"{label} price")

    def test_net_totals(self):
        cost, margin, price = self.EXPECTED_NET
        t = self.res['totals']
        self.assertAlmostEqual(t['cost'], cost, places=2)
        self.assertAlmostEqual(t['margin'], margin, places=2)
        self.assertAlmostEqual(t['price'], price, places=2)
