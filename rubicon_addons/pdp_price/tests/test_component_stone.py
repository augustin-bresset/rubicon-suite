# -*- coding: utf-8 -*-
from odoo.tests import TransactionCase
from odoo import fields


class TestPriceStone(TransactionCase):         
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))

        cls.currency = cls.env.company.currency_id

        # Types / Marges
        cls.margin_model = cls.env['pdp.margin']
        cls.margin_stone_model = cls.env['pdp.margin.stone']
        
      
        cls.stone_cat = cls.env['pdp.stone.category'].create({
            'code': 'AAA',
            'name': 'Precious'
        })
        
        cls.stone_type = cls.env['pdp.stone.type'].create({
            'code': 'RRR',
            'name': 'Ruby',
            'category_id': cls.stone_cat.id,
        })
        
        cls.stone_shade = cls.env['pdp.stone.shade'].create({
            'code': 'SSD',
            'shade': 'Shade S'
        })
        cls.stone_shape = cls.env['pdp.stone.shape'].create({
            'code': 'SSP',
            'shape': 'Shape S'
        })
        cls.stone_size = cls.env['pdp.stone.size'].create({
            'name': 'Size S'
        })
        
        cls.stone = cls.env['pdp.stone'].create({
            'code': 'SAAA',
            'type_id': cls.stone_type.id,
            'shape_id': cls.stone_shape.id,
            'shade_id': cls.stone_shade.id,
            'size_id': cls.stone_size.id,
            'cost': 10.0,
            'currency_id': cls.currency.id,
        })

        # Composition + lignes de pierre
        cls.compo = cls.env['pdp.product.stone.composition'].create({
            'code': 'Comp A',
        })
        
        cls.line = cls.env['pdp.product.stone'].create({
            'composition_id': cls.compo.id,
            'stone_id': cls.stone.id,
            'pieces': 3,  # 3 pcs * 10 = 30
        })

        cls.product = cls.env['pdp.product'].create({
            'code': 'PRODUCT-TEST',
            'stone_composition_id': cls.compo.id,
            })
        cls.margin = cls.env['pdp.margin'].create({
            'code': 'MARGIN-TEST',
            'name': 'Margin test'
            })
        
        cls.margin_stone_model.create({
            'margin_id': cls.margin.id,
            'stone_type_id': cls.stone_type.id,
            'rate': 1.2,  # +20%
        })

        cls.component = cls.env['pdp.price.stone']

    def test_compute_basic_no_margin(self):
        """Sans marge: cost=30, margin=0, price=30"""
        res = self.component.compute(
            product=self.product,
            margin=None,
            currency=self.currency,
            date=fields.Date.today(),
        )
        self.assertEqual(res['type'], 'stone')
        # arrondi via devise
        self.assertEqual(res['cost'], self.currency.round(30.0))
        self.assertEqual(res['margin'], self.currency.round(0.0))
        self.assertEqual(res['price'], self.currency.round(30.0))

    def test_compute_with_margin_by_stone_type(self):
        """Marge type 20%: cost=30, margin=6, price=36"""
        
        res = self.component.compute(
            product=self.product,
            margin=self.margin,
            currency=self.currency,
            date=fields.Date.today(),
        )
        self.assertEqual(res['type'], 'stone')
        self.assertEqual(res['cost'], self.currency.round(30.0))
        self.assertEqual(res['margin'], self.currency.round(6.0))  # (1.2-1.0)*30
        self.assertEqual(res['price'], self.currency.round(36.0))

    def test_compute_ignores_search_default_context(self):
        """Le composant ne doit pas exploser si un search_default_* est présent dans le contexte."""
        # Simule une ouverture depuis une vue qui aurait injecté un filtre par défaut
        comp = self.component.with_context(search_default_product_id=999)
        margin = None
        res = comp.compute(
            product=self.product,
            margin=margin,
            currency=self.currency,
            date=fields.Date.today(),
        )
        # Le résultat doit être le même que sans marge ni contamination
        self.assertEqual(res['cost'], self.currency.round(30.0))
        self.assertEqual(res['margin'], self.currency.round(0.0))
        self.assertEqual(res['price'], self.currency.round(30.0))
