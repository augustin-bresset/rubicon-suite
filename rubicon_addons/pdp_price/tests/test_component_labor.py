# -*- coding: utf-8 -*-
import unittest
from unittest.mock import patch
from odoo.tests.common import TransactionCase
from odoo import fields


class TestPriceLabor(TransactionCase):
    """
    Unit tests for pdp.price.labor:
      - no costs -> zero payload
      - model-level cost used when product-level cost missing/zero
      - product-level cost overrides model-level cost
      - per-labor-type margin factor (multiplicative rate)
      - currency conversion is invoked
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # Company (not strictly needed but often useful to have)
        cls.company = cls.env.ref('base.main_company')

        # Currency: reuse USD or create a simple one
        Currency = cls.env['res.currency']
        usd = Currency.search([('name', '=', 'USD')], limit=1)
        cls.cur = usd or Currency.create({'name': 'USD', 'symbol': '$', 'rounding': 0.01})

        # Minimal product model & product
        ProdModel = cls.env['pdp.product.model']
        cls.model = ProdModel.create({'code': 'MODEL-X'})

        Product = cls.env['pdp.product']
        cls.product = Product.create({
            'code': 'R132-GA/W',
            'model_id': cls.model.id,
            'metal': 'W',
        })

        # A generic margin header for tests that need one
        Margin = cls.env['pdp.margin']
        cls.margin = Margin.search([], limit=1) or Margin.create({'code':'T', 'name': 'TEST'})

        # Wizard
        cls.PriceLabor = cls.env['pdp.price.labor']
        cls.wizard = cls.PriceLabor.create({})

    # ---------------- helpers ----------------
    def _create_labor_type(self, code='SET', name='Stone Setting'):
        LaborType = self.env['pdp.labor.type']
        return LaborType.create({'code': code, 'name': name})

    def _create_model_cost(self, labor_type, amount, currency=None):
        """
        Create pdp.labor.cost.model for (model, labor_type).
        """
        MCost = self.env['pdp.labor.cost.model']
        return MCost.create({
            'model_id': self.model.id,
            'labor_id': labor_type.id,
            'cost': amount,
            'currency_id': (currency or self.cur).id,
        })

    def _create_product_cost(self, labor_type, amount, currency=None):
        """
        Create pdp.labor.cost.product for (product, labor_type).
        NOTE: If your model actually uses a field named 'model_id' here,
        adapt to match. Typically this should be 'product_id'.
        """
        PCost = self.env['pdp.labor.cost.product']
        return PCost.create({
            'product_id': self.product.id,
            'labor_id': labor_type.id,
            'cost': amount,
            'currency_id': (currency or self.cur).id,
        })

    def _create_margin_labor_rate(self, margin, labor_type, rate_factor):
        """
        Create pdp.margin.labor entry with multiplicative 'rate' (e.g. 1.25 = +25%).
        """
        ML = self.env['pdp.margin.labor']
        return ML.create({
            'margin_id': margin.id,
            'labor_id': labor_type.id,
            'rate': rate_factor,
        })

    # ---------------- tests ----------------
    def test_00_no_costs_any_type_returns_zero(self):
        """If there are labor types but no costs at all, totals must be zero."""
        # Create two types, but no costs
        self._create_labor_type(code='SET', name='Setting')
        self._create_labor_type(code='POL', name='Polishing')

        payload = self.wizard.compute(
            product=self.product, margin=None, currency=self.cur, date=fields.Date.today()
        )
        self.assertEqual(payload['type'], 'labor')
        self.assertEqual(payload['cost'], 0.0)
        self.assertEqual(payload['margin'], 0.0)
        self.assertEqual(payload['price'], 0.0)

    def test_01_model_cost_used_when_product_cost_missing(self):
        """Model-level cost is used when no product-level cost exists."""
        t = self._create_labor_type(code='SET')
        self._create_model_cost(t, 12.0, self.cur)
        # No product cost created

        payload = self.wizard.compute(
            product=self.product, margin=None, currency=self.cur, date=fields.Date.today()
        )
        self.assertEqual(payload['type'], 'labor')
        self.assertEqual(payload['cost'], 12.0)
        self.assertEqual(payload['margin'], 0.0)
        self.assertEqual(payload['price'], 12.0)

    def test_02_model_cost_used_when_product_cost_is_zero(self):
        """Model-level cost is used when product-level cost is present but equals zero."""
        t = self._create_labor_type(code='SET')
        self._create_model_cost(t, 10.0, self.cur)
        self._create_product_cost(t, 0.0, self.cur)  # explicitly zero

        payload = self.wizard.compute(
            product=self.product, margin=None, currency=self.cur, date=fields.Date.today()
        )
        self.assertEqual(payload['cost'], 10.0)
        self.assertEqual(payload['margin'], 0.0)
        self.assertEqual(payload['price'], 10.0)

    def test_03_product_cost_overrides_model_cost(self):
        """
        Product-level cost must override model-level cost when > 0.
        This will FAIL with the current implementation because 'cost' is not
        assigned when cost_product != 0.0 (UnboundLocalError).
        """
        t = self._create_labor_type(code='SET')
        self._create_model_cost(t, 10.0, self.cur)
        self._create_product_cost(t, 40.0, self.cur)  # override

        payload = self.wizard.compute(
            product=self.product, margin=None, currency=self.cur, date=fields.Date.today()
        )
        self.assertEqual(payload['cost'], 40.0)
        self.assertEqual(payload['margin'], 0.0)
        self.assertEqual(payload['price'], 40.0)

    def test_04_margin_applied_per_type_multiplicative(self):
        """
        Margin is (rate - 1) * cost for each labor type.
        Example:
          t1 cost=10 with rate=1.10  -> margin +1.0
          t2 cost=20 with rate=1.50  -> margin +10.0
          total cost=30, margin=11, price=41
        """
        t1 = self._create_labor_type(code='SET')
        t2 = self._create_labor_type(code='POL')

        self._create_model_cost(t1, 10.0, self.cur)
        self._create_model_cost(t2, 20.0, self.cur)

        self._create_margin_labor_rate(self.margin, t1, rate_factor=1.10)
        self._create_margin_labor_rate(self.margin, t2, rate_factor=1.50)

        payload = self.wizard.compute(
            product=self.product, margin=self.margin, currency=self.cur, date=fields.Date.today()
        )
        self.assertEqual(payload['type'], 'labor')
        self.assertEqual(payload['cost'], 30.0)
        self.assertAlmostEqual(payload['margin'], 11.0, places=6)
        self.assertAlmostEqual(payload['price'], 41.0, places=6)

    def test_05_currency_conversion_is_used(self):
        """_convert should be called for each cost line when currencies differ."""
        t = self._create_labor_type(code='SET')
        other_cur = self.env['res.currency'].create({'name': 'ZZZ', 'symbol': 'Z', 'rounding': 0.01})

        # Put the cost in ZZZ and mock conversion to return 25.0
        self._create_model_cost(t, 10.0, other_cur)

        with patch.object(type(self.wizard), '_convert', autospec=True) as mock_conv:
            mock_conv.return_value = 25.0
            payload = self.wizard.compute(
                product=self.product, margin=None, currency=self.cur, date=fields.Date.today()
            )

        self.assertEqual(payload['cost'], 25.0)
        self.assertEqual(payload['margin'], 0.0)
        self.assertEqual(payload['price'], 25.0)
        self.assertTrue(mock_conv.called)
