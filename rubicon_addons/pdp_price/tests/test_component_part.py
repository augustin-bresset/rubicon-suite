# -*- coding: utf-8 -*-
import unittest
from unittest.mock import patch
from odoo.tests.common import TransactionCase
from odoo import fields


class TestPricePart(TransactionCase):
    """
    Unit tests for pdp.price.part wizard:
      - no parts -> zero payload
      - cost sum (qty * unit_cost) without margin
      - default quantity = 1.0
      - fallback purity to 18K
      - currency conversion call
      - parts margin factor via pdp.margin.part (new)
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # Company
        Company = cls.env.ref('base.main_company')
        cls.company = Company

        # Currency (USD or create one if missing)
        Currency = cls.env['res.currency']
        usd = Currency.search([('name', '=', 'USD')], limit=1)
        cls.cur = usd or Currency.create({'name': 'USD', 'symbol': '$', 'rounding': 0.01})

        # Purity (18K fallback)
        Purity = cls.env['pdp.metal.purity']
        cls.purity_18k = Purity.search([('code', '=', '18K')], limit=1) or Purity.create({
            'code': '18K',
            'percent' : 0.75
        })

        # Product model and product
        ProdModel = cls.env['pdp.product.model']
        cls.model = ProdModel.create({'code': 'MODEL-X'})  # minimal fields

        Product = cls.env['pdp.product']
        cls.product = Product.create({
            'code': 'R132-GA/W',
            'model_id': cls.model.id,
            'metal': 'W',  # "metal_version" for mapping (e.g. white gold)
        })

        # Model ↔ metal version ↔ purity link (non-fallback case)
        ModelMetal = cls.env['pdp.product.model.metal']
        cls.model_metal_line = ModelMetal.create({
            'model_id': cls.model.id,
            'metal_version': 'W',
            'purity_id': cls.purity_18k.id,
            'weight': 10.0,
        })

        # Base parts
        Part = cls.env['pdp.part']
        cls.part_a = Part.create({'code': 'CA', 'name': 'Clasp A'})
        cls.part_b = Part.create({'code': 'CB', 'name': 'Clasp B'})

        # A margin record to use when needed in tests
        Margin = cls.env['pdp.margin']
        cls.margin = Margin.search([], limit=1) or Margin.create({'code': 'T', 'name': 'TEST'})

        # Wizard record
        cls.PricePart = cls.env['pdp.price.part']
        cls.wizard = cls.PricePart.create({})

    # ----------------- helpers -----------------
    def _create_product_part(self, part, qty=1.0):
        ProdPart = self.env['pdp.product.part']
        return ProdPart.create({
            'product_id': self.product.id,
            'part_id': part.id,
            'quantity': qty,
        })

    def _create_part_cost(self, part, purity, cost, currency=None):
        PartCost = self.env['pdp.part.cost']
        return PartCost.create({
            'part_id': part.id,
            'purity_id': purity.id,
            'cost': cost,
            'currency_id': (currency or self.cur).id,
        })

    def _create_margin_part_factor(self, margin, rate_factor):
        """
        Create a pdp.margin.part entry.
        `rate_factor` is multiplicative (e.g., 1.20 means +20%).
        """
        MarginPart = self.env['pdp.margin.part']
        return MarginPart.create({
            'margin_id': margin.id,
            'rate': rate_factor,
        })

    # ----------------- tests -----------------
    def test_00_no_parts_returns_zero(self):
        """If the product has no parts, the wizard must return a zero payload."""
        payload = self.wizard.compute(
            product=self.product,
            margin=None,
            currency=self.cur,
            date=fields.Date.today()
        )
        self.assertEqual(payload['type'], 'part')
        self.assertEqual(payload['cost'], 0.0)
        self.assertEqual(payload['margin'], 0.0)
        self.assertEqual(payload['price'], 0.0)

    def test_01_sum_costs_no_margin(self):
        """Sum of costs (qty * unit_cost), with no margin applied when margin=None."""
        self._create_product_part(self.part_a, qty=2.0)
        self._create_product_part(self.part_b, qty=3.0)
        self._create_part_cost(self.part_a, self.purity_18k, 10.0, self.cur)  # 2 * 10 = 20
        self._create_part_cost(self.part_b, self.purity_18k, 5.0, self.cur)   # 3 * 5  = 15

        payload = self.wizard.compute(
            product=self.product,
            margin=None,
            currency=self.cur,
            date=fields.Date.today()
        )
        self.assertEqual(payload['type'], 'part')
        self.assertEqual(payload['margin'], 0.0)
        self.assertEqual(payload['cost'], 35.0)   # 20 + 15
        self.assertEqual(payload['price'], 35.0)  # cost + 0

    def test_02_quantity_default_is_one(self):
        """Default quantity = 1.0 when the line does not specify quantity."""
        ProdPart = self.env['pdp.product.part']
        ProdPart.create({
            'product_id': self.product.id,
            'part_id': self.part_a.id,
            # no 'quantity' field set
        })
        self._create_part_cost(self.part_a, self.purity_18k, 12.5, self.cur)

        payload = self.wizard.compute(
            product=self.product,
            margin=None,
            currency=self.cur,
            date=fields.Date.today()
        )
        self.assertEqual(payload['cost'], 12.5)
        self.assertEqual(payload['price'], 12.5)

    def test_03_fallback_purity_18k_when_mapping_missing(self):
        """If no model.metal/purity line is found, fallback to 18K purity."""
        self.product.metal = 'Y'  # no line for W→Y mapping
        self._create_product_part(self.part_a, qty=1.0)
        self._create_part_cost(self.part_a, self.purity_18k, 7.0, self.cur)

        payload = self.wizard.compute(
            product=self.product,
            margin=None,
            currency=self.cur,
            date=fields.Date.today()
        )
        # If fallback worked, cost should be 7
        self.assertEqual(payload['cost'], 7.0)

    def test_04_currency_conversion_is_used(self):
        """Check that _convert is called when the part cost currency differs."""
        self._create_product_part(self.part_a, qty=2.0)
        other_cur = self.env['res.currency'].create({
            'name': 'ZZZ',
            'symbol': 'Z',
            'rounding': 0.01
        })
        self._create_part_cost(self.part_a, self.purity_18k, 10.0, other_cur)

        with patch.object(type(self.wizard), '_convert', autospec=True) as mock_conv:
            # simulate a 2x conversion rate: 10 ZZZ -> 20 USD (per unit)
            mock_conv.return_value = 20.0
            payload = self.wizard.compute(
                product=self.product,
                margin=None,
                currency=self.cur,
                date=fields.Date.today()
            )
            # 2 units * (convert(10 ZZZ) = 20 USD) => 40
            self.assertEqual(payload['cost'], 40.0)
            self.assertEqual(payload['price'], 40.0)
            self.assertTrue(mock_conv.called)

    def test_05_parts_margin_factor_applied(self):
        """
        When a margin is provided and pdp.margin.part exists with a multiplicative
        `rate` (e.g., 1.20 = +20%), the wizard must add (rate - 1) * parts_cost.
        """
        # Parts cost: 2 * 10 + 1 * 5 = 25
        self._create_product_part(self.part_a, qty=2.0)
        self._create_product_part(self.part_b, qty=1.0)
        self._create_part_cost(self.part_a, self.purity_18k, 10.0, self.cur)
        self._create_part_cost(self.part_b, self.purity_18k, 5.0, self.cur)

        # Configure margin factor = 1.20 (+20%)
        self._create_margin_part_factor(self.margin, rate_factor=1.20)

        payload = self.wizard.compute(
            product=self.product,
            margin=self.margin,
            currency=self.cur,
            date=fields.Date.today()
        )
        self.assertEqual(payload['type'], 'part')
        self.assertEqual(payload['cost'], 25.0)
        self.assertAlmostEqual(payload['margin'], 5.0, places=6)  # (1.20 - 1.0) * 25 = 5
        self.assertAlmostEqual(payload['price'], 30.0, places=6)

    def test_06_parts_margin_defaults_to_zero_without_config(self):
        """
        If a margin record is passed but no pdp.margin.part exists,
        the parts margin must be zero.
        """
        # Parts cost: 3 * 4 = 12
        self._create_product_part(self.part_a, qty=3.0)
        self._create_part_cost(self.part_a, self.purity_18k, 4.0, self.cur)

        # No pdp.margin.part created on purpose
        payload = self.wizard.compute(
            product=self.product,
            margin=self.margin,
            currency=self.cur,
            date=fields.Date.today()
        )
        self.assertEqual(payload['cost'], 12.0)
        self.assertEqual(payload['margin'], 0.0)
        self.assertEqual(payload['price'], 12.0)
