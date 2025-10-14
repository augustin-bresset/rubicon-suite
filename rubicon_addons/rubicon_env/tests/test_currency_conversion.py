from odoo.tests.common import TransactionCase
from odoo import fields

class TestCurrencyConversion(TransactionCase):
    """
    Generic tests to ensure that currency conversion:
      - depends on the given date
      - uses the correct rates from res.currency.rate
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.usd = cls.env.ref("base.USD")
        cls.eur = cls.env.ref("base.EUR")

    def test_01_conversion_differs_by_date(self):
        """Two different dates with different rates must produce different results."""

        # Create two EUR rates at different dates
        Rate = self.env["res.currency.rate"]
        Rate.create({
            "currency_id": self.eur.id,
            "name": "2022-10-08",          # 8th October 2022
            "company_id": self.company.id,
            "rate": 1.03,                  # Example rate
        })
        Rate.create({
            "currency_id": self.eur.id,
            "name": "2025-09-01",          # 1st September 2025
            "company_id": self.company.id,
            "rate": 0.95,                  # Example rate
        })

        amount = 100.0
        d1 = fields.Date.from_string("2022-10-08")
        d2 = fields.Date.from_string("2025-09-01")

        # Convert 100 USD → EUR at both dates
        val1 = self.usd._convert(amount, self.eur, self.company, d1)
        val2 = self.usd._convert(amount, self.eur, self.company, d2)

        # The two results must differ, because the rates are different
        self.assertNotEqual(val1, val2)

        # Ensure conversion matches Odoo's internal rate computation
        r1 = self.env["res.currency"]._get_conversion_rate(self.usd, self.eur, self.company, d1)
        r2 = self.env["res.currency"]._get_conversion_rate(self.usd, self.eur, self.company, d2)

        # val = amount * rate
        self.assertAlmostEqual(val1, amount * r1, places=6)
        self.assertAlmostEqual(val2, amount * r2, places=6)

    def test_02_conversion_differs_by_currency(self):
        """Conversion must differ when changing the target currency."""

        # Ensure we have THB in the system (create it if missing)
        thb = self.env["res.currency"].search([("name", "=", "THB")], limit=1)
        if not thb:
            thb = self.env["res.currency"].create({
                "name": "THB",
                "symbol": "฿",
                "rounding": 0.01,
            })

        amount = 100.0
        date = fields.Date.today()

        # Convert 100 USD to EUR and THB on the same date
        val_eur = self.usd._convert(amount, self.eur, self.company, date)
        val_thb = self.usd._convert(amount, thb, self.company, date)

        # Results must differ unless the EUR and THB rates are identical (very unlikely)
        self.assertNotEqual(val_eur, val_thb)

        # Double-check using Odoo's internal conversion rate function
        r_eur = self.env["res.currency"]._get_conversion_rate(self.usd, self.eur, self.company, date)
        r_thb = self.env["res.currency"]._get_conversion_rate(self.usd, thb, self.company, date)

        self.assertAlmostEqual(val_eur, amount * r_eur, places=1)
        self.assertAlmostEqual(val_thb, amount * r_thb, places=1)
