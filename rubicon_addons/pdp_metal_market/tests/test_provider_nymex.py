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
        cls.gold = metal_model.search([('code', '=', 'XAU')], limit=1)
        cls.silver = metal_model.search([('code', '=', 'XAG')], limit=1)

    def test_update_prices_creates_records(self):
        with patch.object(self.provider.__class__, "_get_metal_prices", return_value={"XAU": 2350.50, "XAG": 32.10}):
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
        with patch.object(self.provider.__class__, "_get_metal_prices", return_value={"XAU": 2000.0}):
            first_batch = self.provider.update_prices(codes=["XAU"], day=self.day)
        self.assertEqual(first_batch.price, 2000.0)

        with patch.object(self.provider.__class__, "_get_metal_prices", return_value={"XAU": 2100.0}):
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
        
def test_export_prices_csv(self):
        prices = self.env["pdp.market.price"]
        prices.create({
            "metal_id": self.gold.id,
            "date": self.day,
            "price": 4000.0,
            "source_id": self.env["pdp.market.source"].create({"name": "Test", "type": "api"}).id,
        })
        prices.create({
            "metal_id": self.silver.id,
            "date": self.day,
            "price": 50.0,
            "source_id": self.env["pdp.market.source"].search([], limit=1).id,
        })

        csv_data = prices.export_prices_csv(start_date=self.day, end_date=self.day)
        expected = """date,Gold,Silver\n23-11-2025,4000.0,50.0\n"""
        self.assertEqual(csv_data, expected)
