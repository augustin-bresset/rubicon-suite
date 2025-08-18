# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase
from odoo import fields

class TestPriceAddon(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.cur = cls.env.company.currency_id
        cls.addon_model = cls.env['pdp.addon.type']          # adapte si besoin
        cls.cost_model  = cls.env['pdp.addon.cost']     # idem

        # données
        cls.addon_a = cls.addon_model.create({
            'code': 'E',
            'name': 'Engraving',
            })
        cls.addon_b = cls.addon_model.create({
            'code': 'L',
            'name': 'Laser',
            })
        
        cls.product = cls.env['pdp.product'].create({
            'code': 'R1',
            })

        cls.cost_model.create({
            'product_id': cls.product.id,
            'addon_id': cls.addon_a.id,
            'currency_id': cls.cur.id,
            'cost': 10.0,
        })
        
        cls.cost_model.create({
            'product_id': cls.product.id,
            'addon_id': cls.addon_b.id,
            'currency_id': cls.cur.id,
            'cost': 5.0,
        })

        cls.component = cls.env['pdp.price.addon']

    def test_basic_no_margin(self):
        res = self.component.compute(
            product=self.product, margin=None,
            currency=self.cur, date=fields.Date.today(),
        )
        self.assertEqual(res['type'], 'addon')
        self.assertEqual(res['cost'], self.cur.round(15.0))
        self.assertEqual(res['margin'], self.cur.round(0.0))
        self.assertEqual(res['price'], self.cur.round(15.0))

    def test_with_margin(self):
        margin = self.env['pdp.margin'].create({
            'code': 'M',
            'name': 'Wholesale'
            })
        self.env['pdp.margin.addon'].create({
            'margin_id': margin.id,
            'addon_id': self.addon_a.id,
            'rate': 1.20,  # +20%
        })
        self.env['pdp.margin.addon'].create({
            'margin_id': margin.id,
            'addon_id': self.addon_b.id,
            'rate': 1.20,  # +20%
        })
        res = self.component.compute(
            product=self.product, margin=margin,
            currency=self.cur, date=fields.Date.today(),
        )
        self.assertEqual(res['cost'], self.cur.round(15.0))
        self.assertEqual(res['margin'], self.cur.round(3.0))  # 20% de 15
        self.assertEqual(res['price'], self.cur.round(18.0))

    def test_ignores_search_default_context(self):
        comp = self.component.with_context(search_default_product_id=999)
        res = comp.compute(
            product=self.product, margin=None,
            currency=self.cur, date=fields.Date.today(),
        )
        self.assertEqual(res['cost'], self.cur.round(15.0))

