# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase
from odoo import fields

OZ_TO_G = 31.1034768

class TestPriceMetal(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.currency = cls.env.company.currency_id

        # Métal (coût exprimé en USD/oz)
        cls.metal = cls.env['pdp.metal'].create({
            'name': 'Gold',
            'code': 'G',
            'cost': 2000.0,  # USD / ounce
        })

        # Pureté
        cls.purity = cls.env['pdp.metal.purity'].create({
            'code': '18K',
            'percent': 0.75,
        })

        # Modèle et rel métal
        cls.model = cls.env['pdp.product.model'].create({
            'code': 'R1'
            })
        cls.rel = cls.env['pdp.product.model.metal'].create({
            'model_id': cls.model.id,
            'metal_id': cls.metal.id,
            'purity_id': cls.purity.id,
            'metal_version': 'W',   # adapte selon ton selection/char
            'weight': 10.0,         # grammes
        })

        # Produit qui référence le modèle + la version de métal
        cls.product = cls.env['pdp.product'].create({
            'code': 'PROD-TEST',
            'model_id': cls.model.id,
            'metal': 'W',           # même valeur que rel.metal_version
        })

        cls.component = cls.env['pdp.price.metal']

    def test_basic_no_margin(self):
        res = self.component.compute(
            product=self.product, margin=None,
            currency=self.currency, date=fields.Date.today(),
        )
        self.assertEqual(res['type'], 'metal')
        self.assertGreater(res['cost'], 0.0)
        self.assertEqual(res['margin'], self.currency.round(0.0))
        self.assertEqual(res['price'], self.currency.round(res['cost']))

    def test_with_margin(self):
        margin = self.env['pdp.margin'].create({
            'name': 'Wholesale',
            'code': 'M'
            })
        self.env['pdp.margin.metal'].create({
            'margin_id': margin.id,
            'metal_purity_id': self.purity.id,
            'rate': 1.10,  # +10%
        })
        res = self.component.compute(
            product=self.product, margin=margin,
            currency=self.currency, date=fields.Date.today(),
        )
        self.assertEqual(res['type'], 'metal')
        self.assertGreater(res['cost'], 0.0)
        self.assertEqual(res['margin'], self.currency.round(res['cost'] * 0.10))
        self.assertAlmostEqual(res['price'], res['cost'] + res['margin'], places=6)

    def test_ignores_search_default_context(self):
        comp = self.component.with_context(search_default_product_id=999)
        res = comp.compute(
            product=self.product, margin=None,
            currency=self.currency, date=fields.Date.today(),
        )
        self.assertGreater(res['cost'], 0.0)
