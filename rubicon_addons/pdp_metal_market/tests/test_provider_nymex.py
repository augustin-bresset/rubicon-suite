from unittest.mock import patch

from odoo import fields
from odoo.tests.common import TransactionCase


class TestMarketProviderNY(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.currency = cls.env.ref("base.USD")
        cls.provider = cls.env["pdp.market.provider.nymex"]
        cls.day = fields.Date.from_string("2024-06-01")

        metal_model = cls.env["pdp.market.metal"]
        cls.gold = metal_model.create({
            "name": "Gold",
            "code": "XAU",
            "base_unit": "troy_oz",
            "base_currency_id": cls.currency.id,
        })
        cls.silver = metal_model.create({
            "name": "Silver",
            "code": "XAG",
            "base_unit": "troy_oz",
            "base_currency_id": cls.currency.id,
        })

    def test_update_prices_creates_records(self):
        with patch.object(self.provider, "_get_metal_prices", return_value={"XAU": 2350.50, "XAG": 32.10}):
            prices = self.provider.update_prices(day=self.day)
        self.assertEqual(len(prices), 2)

        gold_price = prices.filtered(lambda p: p.metal_id == self.gold)
        self.assertEqual(gold_price.price, 2350.50)
        self.assertEqual(gold_price.currency_id, self.currency)
        self.assertEqual(gold_price.date, self.day)

        silver_price = prices.filtered(lambda p: p.metal_id == self.silver)
        self.assertEqual(silver_price.price, 32.10)
        self.assertEqual(silver_price.source_id.type, "api")

    def test_update_prices_overwrites_existing(self):
        with patch.object(self.provider, "_get_metal_prices", return_value={"XAU": 2000.0}):
            first_batch = self.provider.update_prices(codes=["XAU"], day=self.day)
        self.assertEqual(first_batch.price, 2000.0)

        with patch.object(self.provider, "_get_metal_prices", return_value={"XAU": 2100.0}):
            updated = self.provider.update_prices(codes=["XAU"], day=self.day)
        self.assertEqual(len(updated), 1)
        self.assertEqual(updated.price, 2100.0)

    def test_normalize_payload_tolerates_invalid_entries(self):
        payload = {
            "rates": {
                "XPT": {"price": "980.5"},
                "XPD": None,
                "BAD": {"price": "not-a-number"},
            }
        }
        normalized = self.provider._normalize_payload(payload)
        self.assertEqual(normalized, {"XPT": 980.5})