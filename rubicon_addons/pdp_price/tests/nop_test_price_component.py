# tests/test_price_components.py
from odoo.tests import TransactionCase   # <-- remplace SavepointCase
from odoo import fields
from datetime import date

class TestPriceComponents(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.USD = cls.env.ref('base.USD')
        cls.company = cls.env.company
        cls.cur = cls.company.currency_id
        # Fixtures minimales
        cls.product = cls.env['pdp.product'].create({
            'code': 'PRODUCT-TEST'
            })
        cls.margin = cls.env['pdp.margin'].create({
            'code': 'MARGIN-TEST',
            'name': 'Margin test'
            })
        # Exemple: un addon cost en USD
        addon = cls.env['pdp.addon'].create({'name': 'Clasp'})
        cls.env['pdp.addon.cost'].create({
            'product_id': cls.product.id,
            'addon_id': addon.id,
            'currency_id': cls.USD.id,
            'cost': 100.0,
        })
        cls.env['pdp.margin.addon'].create({
            'margin_id': cls.margin.id,
            'addon_id': addon.id,
            'rate': 1.25,  # +25%
        })

    def test_addon_component(self):
        comp = self.env['pdp.price.addon']
        out = comp.compute(product=self.product, margin=self.margin,
                           currency=self.cur, date=date.today())
        self.assertIn('cost', out)
        self.assertGreater(out['cost'], 0.0)
        self.assertAlmostEqual(out['price'], out['cost'] + out['margin'], places=4)
        # Vérifie que la marge est bien 25% du coût
        if out['cost']:
            self.assertAlmostEqual(out['margin'], round(out['cost']*0.25, 2), places=2)

    def test_preview_flow(self):
        wiz = self.env['pdp.price.preview'].create({
            'product_id': self.product.id,
            'margin_id': self.margin.id,
            'currency_id': self.cur.id,
        })
        wiz.action_compute()
        self.assertTrue(wiz.line_ids, "Preview should generate lines")
        self.assertAlmostEqual(wiz.price, wiz.cost + wiz.margin, places=4)
