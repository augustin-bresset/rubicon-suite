from odoo.tests import TransactionCase
from odoo import fields


class TestPriceRecutting(TransactionCase):
    """Self-contained checks of the recutting component.

    Uses controlled stones — one above the minimum and one below it — so the
    per-stone floor and the per-piece charge are actually exercised (the R132
    reference product can't: all its recut stones sit below the minimum, so
    the floor dominates and the formula's weight-dependence is never tested).
    All values are in one currency, so the result is hand-derivable.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.usd = cls.env.ref('base.USD')

        # Recutting config: $10 / ct, minimum 0.25 ct per piece.
        cls.config = cls.env['pdp.stone.recutting.config'].get_config()
        cls.config.write({'cost': 10.0, 'currency_id': cls.usd.id, 'min_weight': 0.25})

        cls.margin = cls.env['pdp.margin'].create({
            'code': 'RECT', 'name': 'Recutting Test',
            'labor_metal_rate': 1.0, 'labor_stone_rate': 2.0,
        })

        stype = cls.env['pdp.stone.type'].create({'code': 'RT', 'name': 'Rec Type'})
        sshape = cls.env['pdp.stone.shape'].create({'code': 'RS', 'shape': 'Rec Shape'})
        ssize = cls.env['pdp.stone.size'].create({'name': 'Rec Size'})
        cls.stone = cls.env['pdp.stone'].create({
            'code': 'RT-RS-RecSize', 'type_id': stype.id,
            'shape_id': sshape.id, 'size_id': ssize.id,
        })

        cls.comp = cls.env['pdp.product.stone.composition'].create({'code': 'REC-COMP'})
        # above minimum, below minimum (floored), and not recut (excluded).
        for pieces, rw in ((2, 1.0), (3, 0.1), (5, 0.0)):
            cls.env['pdp.product.stone'].create({
                'composition_id': cls.comp.id, 'stone_id': cls.stone.id,
                'pieces': pieces, 'reshaped_weight': rw,
            })
        cls.product = cls.env['pdp.product'].create({
            'code': 'REC-PROD', 'stone_composition_id': cls.comp.id,
        })

    def _recutting(self):
        return self.env['pdp.price.recutting'].compute(
            product=self.product, margin=self.margin,
            currency=self.usd, date=fields.Date.today())

    def test_floor_per_piece_and_stone_labor_margin(self):
        # large: max(0.25, 1.0) * 2 = 2.0
        # small: max(0.25, 0.1) * 3 = 0.75   (floored)
        # zero reshaped weight: excluded
        # cost = 10 * (2.0 + 0.75) = 27.5 ; margin = (2.0 - 1) * 27.5 = 27.5
        r = self._recutting()
        self.assertAlmostEqual(r['cost'], 27.5, places=2)
        self.assertAlmostEqual(r['margin'], 27.5, places=2)
        self.assertAlmostEqual(r['price'], 55.0, places=2)

    def test_min_weight_is_a_configurable_parameter(self):
        # Raise the minimum to 0.5: large stays 1.0, small floors to 0.5.
        # cost = 10 * (1.0 * 2 + 0.5 * 3) = 10 * 3.5 = 35.0
        self.config.write({'min_weight': 0.5})
        self.assertAlmostEqual(self._recutting()['cost'], 35.0, places=2)

    def test_zero_minimum_charges_the_actual_weight(self):
        # min_weight = 0: nothing is floored.
        # cost = 10 * (1.0 * 2 + 0.1 * 3) = 10 * 2.3 = 23.0
        self.config.write({'min_weight': 0.0})
        self.assertAlmostEqual(self._recutting()['cost'], 23.0, places=2)
