# -*- coding: utf-8 -*-
from odoo.tests import TransactionCase
from odoo import fields


class TestPriceStone(TransactionCase):         
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))

        cls.currency = cls.env.company.currency_id

        # Types / Margins
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

        # Composition + stone lines
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
        """No margin: cost=30, margin=0, price=30"""
        res = self.component.compute(
            product=self.product,
            margin=None,
            currency=self.currency,
            date=fields.Date.today(),
        )
        self.assertEqual(res['type'], 'stone')
        # rounded via currency
        self.assertEqual(res['cost'], self.currency.round(30.0))
        self.assertEqual(res['margin'], self.currency.round(0.0))
        self.assertEqual(res['price'], self.currency.round(30.0))

    def test_compute_with_margin_by_stone_type(self):
        """Type margin 20%: cost=30, margin=6, price=36"""
        
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
        """The component must not blow up if a search_default_* is present in the context."""
        # Simulate an opening from a view that would have injected a default filter
        comp = self.component.with_context(search_default_product_id=999)
        margin = None
        res = comp.compute(
            product=self.product,
            margin=margin,
            currency=self.currency,
            date=fields.Date.today(),
        )
        # The result must be the same as without margin or contamination
        self.assertEqual(res['cost'], self.currency.round(30.0))
        self.assertEqual(res['margin'], self.currency.round(0.0))
        self.assertEqual(res['price'], self.currency.round(30.0))

    def test_compute_with_conditional_margin_applied(self):
        """Conditional margin applied because cost > comparative_cost"""
        cond_margin = self.env['pdp.margin.stone.conditional'].create({
            'margin_id': self.margin.id,
            'stone_cat_id': self.stone_cat.id,
            'comparative_cost': 20.0,  # threshold
            'currency_id': self.currency.id,
            'operator': '>' ,  # if cost > comparative_cost
            'rate': 1.5,       # +50%
        })
        # our product: cost=30, so > 20 → conditional margin 50% * 30 = 15
        res = self.component.compute(
            product=self.product,
            margin=self.margin,
            currency=self.currency,
            date=fields.Date.today(),
        )
        self.assertEqual(res['cost'], self.currency.round(30.0))
        self.assertEqual(res['margin'], self.currency.round(15.0))
        self.assertEqual(res['price'], self.currency.round(45.0))

    def test_compute_with_conditional_margin_not_applied(self):
        """Conditional margin ignored because cost <= comparative_cost"""
        cond_margin = self.env['pdp.margin.stone.conditional'].create({
            'margin_id': self.margin.id,
            'stone_cat_id': self.stone_cat.id,
            'comparative_cost': 50.0,  # threshold too high
            'currency_id': self.currency.id,
            'operator': '>' ,
            'rate': 1.5,
        })
        # cost=30 ≤ 50 → condition not met → fallback type margin 20%
        res = self.component.compute(
            product=self.product,
            margin=self.margin,
            currency=self.currency,
            date=fields.Date.today(),
        )
        self.assertEqual(res['cost'], self.currency.round(30.0))
        self.assertEqual(res['margin'], self.currency.round(6.0))  # fallback type
        self.assertEqual(res['price'], self.currency.round(36.0))

    def test_compute_with_conditional_margin_operator_less(self):
        """Conditional margin applied with operator '<'"""
        cond_margin = self.env['pdp.margin.stone.conditional'].create({
            'margin_id': self.margin.id,
            'stone_cat_id': self.stone_cat.id,
            'comparative_cost': 40.0,
            'currency_id': self.currency.id,
            'operator': '<',   # if cost < comparative_cost
            'rate': 1.3,       # +30%
        })
        # cost=30 < 40 → condition met → 30% * 30 = 9
        res = self.component.compute(
            product=self.product,
            margin=self.margin,
            currency=self.currency,
            date=fields.Date.today(),
        )
        self.assertEqual(res['cost'], self.currency.round(30.0))
        self.assertEqual(res['margin'], self.currency.round(9.0))
        self.assertEqual(res['price'], self.currency.round(39.0))

    def test_compute_stone_margin_shape_exact_match(self):
        """A margin line with type+shape matches over a type-only line."""
        # Add a type+shape specific line with higher rate
        self.env['pdp.margin.stone'].create({
            'margin_id': self.margin.id,
            'stone_type_id': self.stone_type.id,
            'stone_shape_id': self.stone_shape.id,
            'rate': 1.5,  # more specific: +50%
        })
        # The existing line has type only (rate=1.2). The new line has type+shape.
        # Our stone has both type and shape set → should pick the type+shape line (1.5).
        res = self.component.compute(
            product=self.product,
            margin=self.margin,
            currency=self.currency,
            date=fields.Date.today(),
        )
        # cost=30, rate=1.5, margin=0.5*30=15
        self.assertEqual(res['cost'], self.currency.round(30.0))
        self.assertEqual(res['margin'], self.currency.round(15.0))
        self.assertEqual(res['price'], self.currency.round(45.0))

    def test_compute_stone_margin_shape_fallback_to_type_only(self):
        """When no line matches the stone's shape, falls back to type-only line."""
        other_shape = self.env['pdp.stone.shape'].create({'code': 'OTH', 'shape': 'Other'})
        # Add a line for a DIFFERENT shape — should NOT match our stone
        self.env['pdp.margin.stone'].create({
            'margin_id': self.margin.id,
            'stone_type_id': self.stone_type.id,
            'stone_shape_id': other_shape.id,
            'rate': 2.0,
        })
        # Only type-only line (rate=1.2) should match our stone's shape
        res = self.component.compute(
            product=self.product,
            margin=self.margin,
            currency=self.currency,
            date=fields.Date.today(),
        )
        self.assertEqual(res['cost'], self.currency.round(30.0))
        self.assertEqual(res['margin'], self.currency.round(6.0))   # fallback: 1.2 rate
        self.assertEqual(res['price'], self.currency.round(36.0))
